output "api_documents_url" {
  description = "URL endpoint GET/POST /documents"
  value       = module.api_gateway.documents_url
}

output "api_id" {
  description = "ID REST API (dùng để cập nhật frontend)"
  value       = module.api_gateway.api_id
}

output "s3_bucket" {
  description = "Tên S3 bucket"
  value       = module.storage.bucket_name
}

output "dynamodb_table" {
  description = "Tên bảng DynamoDB"
  value       = module.storage.table_name
}

output "frontend_url" {
  description = "URL truy cập website"
  value       = "http://localhost:4566/${module.storage.bucket_name}/frontend/index.html"
}

output "cloudfront_domain" {
  description = "Domain CloudFront CDN — dùng thay localhost:4566 để truy cập file qua CDN"
  value       = module.storage.cloudfront_domain_name
}

output "cloudfront_distribution_id" {
  description = "ID CloudFront Distribution"
  value       = module.storage.cloudfront_distribution_id
}

output "upload_frontend_command" {
  description = "Lệnh upload frontend lên S3 (chạy sau terraform apply)"
  value       = "aws --endpoint-url=http://localhost:4566 s3 cp ../frontend/index.html s3://${module.storage.bucket_name}/frontend/index.html"
}
