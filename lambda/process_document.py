import json
import boto3
import os
import time
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

LOCALSTACK_ENDPOINT = os.environ.get("LOCALSTACK_ENDPOINT", "http://host.docker.internal:4566")
TABLE_NAME = "Documents"

s3 = boto3.client(
    "s3",
    endpoint_url=LOCALSTACK_ENDPOINT,
    region_name="ap-southeast-1",
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

dynamodb = boto3.client(
    "dynamodb",
    endpoint_url=LOCALSTACK_ENDPOINT,
    region_name="ap-southeast-1",
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

def is_image_file(file_name):
    lower_name = file_name.lower()
    return lower_name.endswith(".jpg") or lower_name.endswith(".jpeg") or lower_name.endswith(".png")

def find_document_by_s3_key(s3_key):
    for _ in range(5):
        result = dynamodb.scan(
            TableName=TABLE_NAME,
            FilterExpression="s3_key = :s3_key",
            ExpressionAttributeValues={
                ":s3_key": {"S": s3_key}
            }
        )

        items = result.get("Items", [])
        if items:
            return items

        time.sleep(1)

    return []

def add_watermark_and_compress(bucket_name, s3_key):
    original_object = s3.get_object(
        Bucket=bucket_name,
        Key=s3_key
    )

    image_bytes = original_object["Body"].read()
    image = Image.open(BytesIO(image_bytes)).convert("RGB")

    draw = ImageDraw.Draw(image)
    watermark_text = "Mini LMS Cloud"

    width, height = image.size

    try:
        font = ImageFont.truetype("arial.ttf", max(20, width // 25))
    except:
        font = ImageFont.load_default()

    text_box = draw.textbbox((0, 0), watermark_text, font=font)
    text_width = text_box[2] - text_box[0]
    text_height = text_box[3] - text_box[1]

    x = width - text_width - 20
    y = height - text_height - 20

    draw.rectangle(
        [x - 10, y - 10, x + text_width + 10, y + text_height + 10],
        fill=(0, 0, 0)
    )

    draw.text(
        (x, y),
        watermark_text,
        fill=(255, 255, 255),
        font=font
    )

    output_buffer = BytesIO()

    image.save(
        output_buffer,
        format="JPEG",
        quality=65,
        optimize=True
    )

    file_name_without_ext = os.path.splitext(os.path.basename(s3_key))[0]
    processed_key = "processed/" + file_name_without_ext + "_watermarked.jpg"

    s3.put_object(
        Bucket=bucket_name,
        Key=processed_key,
        Body=output_buffer.getvalue(),
        ContentType="image/jpeg"
    )

    return processed_key

def update_document_status(document_id, status, processed_key=""):
    update_expression = "SET #st = :status_value, processed_time = :processed_time"

    expression_attribute_names = {
        "#st": "status"
    }

    expression_attribute_values = {
        ":status_value": {"S": status},
        ":processed_time": {"S": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    }

    if processed_key:
        update_expression += ", processed_key = :processed_key"
        expression_attribute_values[":processed_key"] = {"S": processed_key}

    dynamodb.update_item(
        TableName=TABLE_NAME,
        Key={
            "document_id": {"S": document_id}
        },
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values
    )

def lambda_handler(event, context):
    try:
        print("S3 Event Received:")
        print(json.dumps(event))

        records = event.get("Records", [])

        for record in records:
            bucket_name = record["s3"]["bucket"]["name"]
            s3_key = record["s3"]["object"]["key"]

            if s3_key.startswith("frontend/"):
                print(f"Skip frontend file: {s3_key}")
                continue

            if s3_key.startswith("processed/"):
                print(f"Skip processed file to avoid loop: {s3_key}")
                continue

            items = find_document_by_s3_key(s3_key)

            if not items:
                print(f"No metadata found for s3_key: {s3_key}")
                continue

            for item in items:
                document_id = item["document_id"]["S"]

                if is_image_file(s3_key):
                    processed_key = add_watermark_and_compress(bucket_name, s3_key)
                    update_document_status(document_id, "processed", processed_key)
                    print(f"Image processed: {s3_key} -> {processed_key}")
                else:
                    update_document_status(document_id, "processed")
                    print(f"Non-image document marked as processed: {s3_key}")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Xu ly S3 Event thanh cong"
            }, ensure_ascii=False)
        }

    except Exception as e:
        print("Error:", str(e))

        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Loi khi xu ly S3 Event",
                "error": str(e)
            }, ensure_ascii=False)
        }