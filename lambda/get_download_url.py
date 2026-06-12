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
            "Access-Control-Allow-Methods": "GET,OPTIONS"
        },
        "body": json.dumps(body, ensure_ascii=False)
    }
    
def fix_url(url):
    return url.replace("host.docker.internal:4566", "localhost:4566") \
              .replace("host.docker.internal", "localhost")


def lambda_handler(event, context):
    try:
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
        file_name = item.get("file_name", {}).get("S", "unknown")

        if not s3_key:
            return cors_response(404, {"message": "Không tìm thấy file trên S3"})

        # Tạo Presigned URL cho file gốc (hết hạn sau 1 giờ)
        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": BUCKET_NAME,
                "Key": s3_key,
                "ResponseContentDisposition": f'attachment; filename="{file_name}"'
            },
            ExpiresIn=3600
        )

        response_data = {
            "message": "Tạo URL tải xuống thành công",
            "document_id": document_id,
            "file_name": file_name,
            "download_url": fix_url(presigned_url),
            "expires_in": "1 giờ"
        }

        # Nếu có ảnh đã watermark, tạo thêm URL cho ảnh đã xử lý
        if processed_key:
            processed_name = processed_key.split("/")[-1]
            processed_url = s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": BUCKET_NAME,
                    "Key": processed_key,
                    "ResponseContentDisposition": f'attachment; filename="{processed_name}"'
                },
                ExpiresIn=3600
            )
            response_data["processed_url"] = fix_url(processed_url)
            response_data["processed_file_name"] = processed_name

        return cors_response(200, response_data)

    except Exception as e:
        print(f"Lỗi tạo presigned URL: {str(e)}")
        return cors_response(500, {
            "message": "Lỗi khi tạo URL tải xuống",
            "error": str(e)
        })
