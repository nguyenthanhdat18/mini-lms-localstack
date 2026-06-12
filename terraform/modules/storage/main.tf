resource "aws_s3_bucket" "documents_bucket" {
  bucket = var.bucket_name
}

resource "aws_s3_bucket_cors_configuration" "documents_cors" {
  bucket = aws_s3_bucket.documents_bucket.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

resource "aws_dynamodb_table" "documents_table" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "document_id"

  attribute {
    name = "document_id"
    type = "S"
  }

  tags = {
    Project     = "mini-lms"
    Environment = "local"
  }
}

# ─────────────── CloudFront Distribution (CDN bọc ngoài S3) ───────────────
# Giả lập trên LocalStack — phục vụ tài liệu học tập với tốc độ cao
resource "aws_cloudfront_distribution" "lms_cdn" {
  # LocalStack: bỏ qua bước chờ deploy để tránh timeout vô hạn
  wait_for_deployment = false

  origin {
    domain_name = "${var.bucket_name}.s3.amazonaws.com"
    origin_id   = "S3-${var.bucket_name}"

    s3_origin_config {
      origin_access_identity = ""
    }
  }

  enabled             = true
  comment             = "CDN cho Mini LMS Cloud — phân phối tài liệu học tập toàn cầu"
  default_root_object = "frontend/index.html"

  # Cache behavior mặc định cho toàn bộ file
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${var.bucket_name}"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    # TTL cho file tĩnh (ảnh, pdf, video)
    min_ttl     = 0
    default_ttl = 86400    # 1 ngày
    max_ttl     = 31536000 # 1 năm
  }

  # Cache behavior riêng cho frontend HTML — TTL ngắn để cập nhật nhanh
  ordered_cache_behavior {
    path_pattern           = "/frontend/*"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${var.bucket_name}"
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 300   # 5 phút — cập nhật UI nhanh hơn
    max_ttl     = 3600  # 1 giờ
  }

  # Không giới hạn khu vực địa lý — phục vụ toàn cầu
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # Dùng certificate mặc định của CloudFront
  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Project     = "mini-lms"
    Environment = "local"
    Purpose     = "CDN-for-media-delivery"
  }
}
