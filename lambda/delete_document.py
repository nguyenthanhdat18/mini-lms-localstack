import json
import boto3
import os

LOCALSTACK_ENDPOINT = os.environ.get("LOCALSTACK_ENDPOINT", "http://host.docker.internal:4566")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "mini-lms-documents")
TABLE_NAME = os.environ.get("TABLE_NAME", "Documents")

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


def cors_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "DELETE,OPTIONS"
        },
        "body": json.dumps(body, ensure_ascii=False)
    }


def lambda_handler(event, context):
    try:
        # Xử lý CORS preflight
        if event.get("httpMethod") == "OPTIONS":
            return cors_response(200, {"message": "CORS OK"})

        # Lấy document_id từ path parameter
        document_id = event.get("pathParameters", {}).get("document_id", "").strip()

        if not document_id:
            return cors_response(400, {"message": "Thiếu document_id"})

        # Tìm metadata trong DynamoDB
        result = dynamodb.get_item(
            TableName=TABLE_NAME,
            Key={"document_id": {"S": document_id}}
        )

        item = result.get("Item")
        if not item:
            return cors_response(404, {"message": "Tài liệu không tồn tại"})

        s3_key = item.get("s3_key", {}).get("S", "")
        processed_key = item.get("processed_key", {}).get("S", "")

        # Xóa file gốc trên S3
        if s3_key:
            try:
                s3.delete_object(Bucket=BUCKET_NAME, Key=s3_key)
            except Exception as e:
                print(f"Cảnh báo: không xóa được file gốc {s3_key}: {str(e)}")

        # Xóa file đã xử lý (ảnh watermark) nếu có
        if processed_key:
            try:
                s3.delete_object(Bucket=BUCKET_NAME, Key=processed_key)
            except Exception as e:
                print(f"Cảnh báo: không xóa được file xử lý {processed_key}: {str(e)}")

        # Xóa metadata trong DynamoDB
        dynamodb.delete_item(
            TableName=TABLE_NAME,
            Key={"document_id": {"S": document_id}}
        )

        return cors_response(200, {
            "message": "Xóa tài liệu thành công",
            "document_id": document_id
        })

    except Exception as e:
        print(f"Lỗi khi xóa tài liệu: {str(e)}")
        return cors_response(500, {
            "message": "Lỗi khi xóa tài liệu",
            "error": str(e)
        })
