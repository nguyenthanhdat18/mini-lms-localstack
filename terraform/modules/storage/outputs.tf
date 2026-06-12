output "bucket_name" {
  description = "Tên S3 bucket"
  value       = aws_s3_bucket.documents_bucket.bucket
}

output "bucket_arn" {
  description = "ARN của S3 bucket"
  value       = aws_s3_bucket.documents_bucket.arn
}

output "table_name" {
  description = "Tên bảng DynamoDB"
  value       = aws_dynamodb_table.documents_table.name
}

output "table_arn" {
  description = "ARN bảng DynamoDB"
  value       = aws_dynamodb_table.documents_table.arn
}

output "cloudfront_domain_name" {
  description = "Domain CloudFront CDN (dùng để truy cập file qua CDN)"
  value       = aws_cloudfront_distribution.lms_cdn.domain_name
}

output "cloudfront_distribution_id" {
  description = "ID CloudFront Distribution"
  value       = aws_cloudfront_distribution.lms_cdn.id
}
