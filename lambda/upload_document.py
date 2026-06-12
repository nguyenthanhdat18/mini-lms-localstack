import json
import boto3
import os
import base64
import uuid
from datetime import datetime

LOCALSTACK_ENDPOINT = os.environ.get("LOCALSTACK_ENDPOINT", "http://host.docker.internal:4566")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "mini-lms-documents")
TABLE_NAME = os.environ.get("TABLE_NAME", "Documents")

# Danh sách định dạng file được phép upload
ALLOWED_EXTENSIONS = {"txt", "pdf", "docx", "doc", "png", "jpg", "jpeg", "gif", "mp4", "mp3"}
MAX_FILE_SIZE_MB = 10

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
            "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS"
        },
        "body": json.dumps(body, ensure_ascii=False)
    }


def lambda_handler(event, context):
    try:
        if event.get("httpMethod") == "OPTIONS":
            return cors_response(200, {"message": "CORS OK"})

        body = event.get("body", "{}")
        if isinstance(body, str):
            data = json.loads(body)
        else:
            data = body

        title = data.get("title", "").strip()
        subject = data.get("subject", "").strip()
        description = data.get("description", "").strip()
        file_name = data.get("file_name", "").strip()
        file_content = data.get("file_content", "")

        # Validate đầu vào
        if not title or not subject or not description or not file_name or not file_content:
            return cors_response(400, {"message": "Thiếu thông tin tài liệu hoặc file"})

        # Validate định dạng file
        file_ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
        if file_ext not in ALLOWED_EXTENSIONS:
            return cors_response(400, {
                "message": f"Định dạng file không được hỗ trợ: .{file_ext}",
                "allowed": list(ALLOWED_EXTENSIONS)
            })

        # Decode base64 và kiểm tra kích thước
        try:
            file_bytes = base64.b64decode(file_content)
        except Exception:
            return cors_response(400, {"message": "Nội dung file không hợp lệ (base64 lỗi)"})

        file_size_mb = len(file_bytes) / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            return cors_response(400, {
                "message": f"File quá lớn ({file_size_mb:.1f} MB). Giới hạn {MAX_FILE_SIZE_MB} MB"
            })

        document_id = str(uuid.uuid4())
        s3_key = file_name
        upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Ghi metadata vào DynamoDB trước để S3 Event không bị lỗi race condition
        dynamodb.put_item(
            TableName=TABLE_NAME,
            Item={
                "document_id": {"S": document_id},
                "title":       {"S": title},
                "subject":     {"S": subject},
                "description": {"S": description},
                "file_name":   {"S": file_name},
                "file_type":   {"S": file_ext},
                "s3_key":      {"S": s3_key},
                "upload_time": {"S": upload_time},
                "file_size":   {"S": f"{file_size_mb:.2f} MB"},
                "status":      {"S": "uploaded"}
            }
        )

        # Upload file lên S3 — S3 Event sẽ tự động kích hoạt process-document
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=file_bytes,
            ContentType=f"application/{file_ext}"
        )

        return cors_response(200, {
            "message": "Upload tài liệu thành công",
            "document": {
                "document_id": document_id,
                "title":       title,
                "subject":     subject,
                "description": description,
                "file_name":   file_name,
                "file_type":   file_ext,
                "s3_key":      s3_key,
                "upload_time": upload_time,
                "file_size":   f"{file_size_mb:.2f} MB",
                "status":      "uploaded"
            }
        })

    except json.JSONDecodeError:
        return cors_response(400, {"message": "Body request không đúng định dạng JSON"})
    except Exception as e:
        print(f"Lỗi upload: {str(e)}")
        return cors_response(500, {
            "message": "Lỗi khi upload tài liệu",
            "error": str(e)
        })
