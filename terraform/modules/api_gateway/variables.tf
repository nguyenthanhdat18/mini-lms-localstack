variable "project_name" {
  description = "Tên project"
  type        = string
}

variable "stage_name" {
  description = "Tên stage API Gateway (dev/prod)"
  type        = string
  default     = "dev"
}

variable "list_documents_invoke_arn" {
  description = "Invoke ARN Lambda list-documents"
  type        = string
}

variable "list_documents_name" {
  description = "Tên Lambda list-documents"
  type        = string
}

variable "upload_document_invoke_arn" {
  description = "Invoke ARN Lambda upload-document"
  type        = string
}

variable "upload_document_name" {
  description = "Tên Lambda upload-document"
  type        = string
}

variable "delete_document_invoke_arn" {
  description = "Invoke ARN Lambda delete-document"
  type        = string
}

variable "delete_document_name" {
  description = "Tên Lambda delete-document"
  type        = string
}

variable "get_download_url_invoke_arn" {
  description = "Invoke ARN Lambda get-download-url"
  type        = string
}

variable "get_download_url_name" {
  description = "Tên Lambda get-download-url"
  type        = string
}
