import json
import boto3
import os

LOCALSTACK_ENDPOINT = os.environ.get("LOCALSTACK_ENDPOINT", "http://host.docker.internal:4566")
TABLE_NAME = os.environ.get("TABLE_NAME", "Documents")

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
        # Lọc theo subject nếu có query string
        query_params = event.get("queryStringParameters") or {}
        filter_subject = query_params.get("subject", "").strip()

        if filter_subject:
            result = dynamodb.scan(
                TableName=TABLE_NAME,
                FilterExpression="subject = :subject",
                ExpressionAttributeValues={":subject": {"S": filter_subject}}
            )
        else:
            result = dynamodb.scan(TableName=TABLE_NAME)

        items = result.get("Items", [])

        documents = []
        for item in items:
            documents.append({
                "document_id": item.get("document_id", {}).get("S", ""),
                "title":       item.get("title",       {}).get("S", ""),
                "subject":     item.get("subject",     {}).get("S", ""),
                "description": item.get("description", {}).get("S", ""),
                "file_name":   item.get("file_name",   {}).get("S", ""),
                "file_type":   item.get("file_type",   {}).get("S", ""),
                "s3_key":      item.get("s3_key",      {}).get("S", ""),
                "upload_time": item.get("upload_time", {}).get("S", ""),
                "file_size":   item.get("file_size",   {}).get("S", ""),
                "status":      item.get("status",      {}).get("S", ""),
                "processed_key": item.get("processed_key", {}).get("S", ""),
            })

        # Sắp xếp mới nhất lên đầu
        documents.sort(key=lambda x: x.get("upload_time", ""), reverse=True)

        return cors_response(200, {
            "message": "Lấy danh sách tài liệu thành công",
            "total": len(documents),
            "documents": documents
        })

    except Exception as e:
        print(f"Lỗi lấy danh sách: {str(e)}")
        return cors_response(500, {
            "message": "Lỗi khi lấy danh sách tài liệu",
            "error": str(e)
        })
