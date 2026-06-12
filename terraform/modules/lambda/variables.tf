variable "project_name" {
  description = "Tên project (dùng làm prefix cho tên tài nguyên)"
  type        = string
}

variable "localstack_endpoint" {
  description = "Endpoint của LocalStack"
  type        = string
  default     = "http://host.docker.internal:4566"
}

variable "bucket_name" {
  description = "Tên S3 bucket"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN của S3 bucket"
  type        = string
}

variable "table_name" {
  description = "Tên bảng DynamoDB"
  type        = string
}

variable "dynamodb_table_arn" {
  description = "ARN bảng DynamoDB"
  type        = string
}

variable "list_documents_zip" {
  description = "Đường dẫn tới file zip của Lambda list-documents"
  type        = string
}

variable "upload_document_zip" {
  description = "Đường dẫn tới file zip của Lambda upload-document"
  type        = string
}

variable "process_document_zip" {
  description = "Đường dẫn tới file zip của Lambda process-document"
  type        = string
}

variable "delete_document_zip" {
  description = "Đường dẫn tới file zip của Lambda delete-document"
  type        = string
}

variable "get_download_url_zip" {
  description = "Đường dẫn tới file zip của Lambda get-download-url"
  type        = string
}
