output "api_id" {
  description = "ID của REST API"
  value       = aws_api_gateway_rest_api.api.id
}

output "stage_name" {
  description = "Tên stage đã deploy"
  value       = aws_api_gateway_stage.dev.stage_name
}

output "documents_url" {
  description = "URL endpoint /documents"
  value       = "http://localhost:4566/restapis/${aws_api_gateway_rest_api.api.id}/${aws_api_gateway_stage.dev.stage_name}/_user_request_/documents"
}

output "download_url_template" {
  description = "URL template cho endpoint tải xuống"
  value       = "http://localhost:4566/restapis/${aws_api_gateway_rest_api.api.id}/${aws_api_gateway_stage.dev.stage_name}/_user_request_/documents/{document_id}/download"
}
