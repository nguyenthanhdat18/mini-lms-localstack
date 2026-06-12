variable "bucket_name" {
  description = "Tên S3 bucket"
  type        = string
  default     = "mini-lms-documents"
}

variable "table_name" {
  description = "Tên bảng DynamoDB"
  type        = string
  default     = "Documents"
}
