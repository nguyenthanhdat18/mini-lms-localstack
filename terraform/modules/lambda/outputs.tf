output "list_documents_arn" {
  description = "ARN Lambda list-documents"
  value       = aws_lambda_function.list_documents.arn
}

output "list_documents_invoke_arn" {
  description = "Invoke ARN Lambda list-documents (dùng cho API Gateway)"
  value       = aws_lambda_function.list_documents.invoke_arn
}

output "upload_document_arn" {
  description = "ARN Lambda upload-document"
  value       = aws_lambda_function.upload_document.arn
}

output "upload_document_invoke_arn" {
  description = "Invoke ARN Lambda upload-document (dùng cho API Gateway)"
  value       = aws_lambda_function.upload_document.invoke_arn
}

output "upload_document_name" {
  description = "Tên Lambda upload-document"
  value       = aws_lambda_function.upload_document.function_name
}

output "list_documents_name" {
  description = "Tên Lambda list-documents"
  value       = aws_lambda_function.list_documents.function_name
}

output "delete_document_invoke_arn" {
  description = "Invoke ARN Lambda delete-document (dùng cho API Gateway)"
  value       = aws_lambda_function.delete_document.invoke_arn
}

output "delete_document_name" {
  description = "Tên Lambda delete-document"
  value       = aws_lambda_function.delete_document.function_name
}

output "get_download_url_invoke_arn" {
  description = "Invoke ARN Lambda get-download-url (dùng cho API Gateway)"
  value       = aws_lambda_function.get_download_url.invoke_arn
}

output "get_download_url_name" {
  description = "Tên Lambda get-download-url"
  value       = aws_lambda_function.get_download_url.function_name
}
