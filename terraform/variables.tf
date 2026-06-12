variable "project_name" {
  description = "Tên project (prefix cho tên tài nguyên AWS)"
  type        = string
  default     = "mini-lms"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-1"
}

variable "localstack_endpoint" {
  description = "Endpoint LocalStack"
  type        = string
  default     = "http://localhost:4566"
}

variable "localstack_endpoint_docker" {
  description = "Endpoint LocalStack dùng bên trong Lambda container"
  type        = string
  default     = "http://host.docker.internal:4566"
}

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

variable "stage_name" {
  description = "Stage API Gateway"
  type        = string
  default     = "dev"
}
