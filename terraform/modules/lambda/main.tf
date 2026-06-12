resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = { Service = "lambda.amazonaws.com" }
      }
    ]
  })

  tags = {
    Project     = var.project_name
    Environment = "local"
  }
}

# IAM Policy áp dụng nguyên tắc Least Privilege
# Mỗi Lambda chỉ được cấp đúng quyền cần thiết, không cấp thừa
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # Quyền ghi log vào CloudWatch Logs (cần cho cả 4 Lambda)
        Sid    = "AllowCloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        # Lambda list-documents: chỉ cần đọc DynamoDB
        Sid    = "AllowDynamoDBRead"
        Effect = "Allow"
        Action = [
          "dynamodb:Scan",
          "dynamodb:GetItem",
          "dynamodb:Query"
        ]
        Resource = var.dynamodb_table_arn
      },
      {
        # Lambda upload-document: cần ghi DynamoDB + upload S3
        # Lambda process-document: cần đọc/ghi S3
        # Lambda delete-document: cần xóa DynamoDB
        Sid    = "AllowDynamoDBWrite"
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem"
        ]
        Resource = var.dynamodb_table_arn
      },
      {
        # Quyền đọc/ghi/xóa S3 chỉ trong bucket của project
        Sid    = "AllowS3BucketAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.s3_bucket_arn,
          "${var.s3_bucket_arn}/*"
        ]
      }
    ]
  })
}

# Lambda list-documents
resource "aws_lambda_function" "list_documents" {
  function_name = "${var.project_name}-list-documents"
  role          = aws_iam_role.lambda_role.arn
  handler       = "list_documents.lambda_handler"
  runtime       = "python3.9"
  timeout       = 10
  memory_size   = 128

  filename         = var.list_documents_zip
  source_code_hash = filebase64sha256(var.list_documents_zip)

  environment {
    variables = {
      LOCALSTACK_ENDPOINT = var.localstack_endpoint
      TABLE_NAME          = var.table_name
      BUCKET_NAME         = var.bucket_name
    }
  }

  tags = {
    Project     = var.project_name
    Function    = "list-documents"
    Environment = "local"
  }
}

# Lambda upload-document
resource "aws_lambda_function" "upload_document" {
  function_name = "${var.project_name}-upload-document"
  role          = aws_iam_role.lambda_role.arn
  handler       = "upload_document.lambda_handler"
  runtime       = "python3.9"
  timeout       = 30
  memory_size   = 256

  filename         = var.upload_document_zip
  source_code_hash = filebase64sha256(var.upload_document_zip)

  environment {
    variables = {
      LOCALSTACK_ENDPOINT = var.localstack_endpoint
      TABLE_NAME          = var.table_name
      BUCKET_NAME         = var.bucket_name
    }
  }

  tags = {
    Project     = var.project_name
    Function    = "upload-document"
    Environment = "local"
  }
}

# Lambda process-document (xử lý ảnh tự động qua S3 Event)
resource "aws_lambda_function" "process_document" {
  function_name = "${var.project_name}-process-document"
  role          = aws_iam_role.lambda_role.arn
  handler       = "process_document.lambda_handler"
  runtime       = "python3.9"
  timeout       = 60
  memory_size   = 512

  filename         = var.process_document_zip
  source_code_hash = filebase64sha256(var.process_document_zip)

  environment {
    variables = {
      LOCALSTACK_ENDPOINT = var.localstack_endpoint
      TABLE_NAME          = var.table_name
      BUCKET_NAME         = var.bucket_name
    }
  }

  tags = {
    Project     = var.project_name
    Function    = "process-document"
    Environment = "local"
  }
}

# Lambda delete-document (xóa tài liệu)
resource "aws_lambda_function" "delete_document" {
  function_name = "${var.project_name}-delete-document"
  role          = aws_iam_role.lambda_role.arn
  handler       = "delete_document.lambda_handler"
  runtime       = "python3.9"
  timeout       = 10
  memory_size   = 128

  filename         = var.delete_document_zip
  source_code_hash = filebase64sha256(var.delete_document_zip)

  environment {
    variables = {
      LOCALSTACK_ENDPOINT = var.localstack_endpoint
      TABLE_NAME          = var.table_name
      BUCKET_NAME         = var.bucket_name
    }
  }

  tags = {
    Project     = var.project_name
    Function    = "delete-document"
    Environment = "local"
  }
}

# Quyền cho S3 gọi Lambda process-document khi có file mới
resource "aws_lambda_permission" "allow_s3_process" {
  statement_id  = "AllowS3InvokeProcessDocument"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.process_document.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = var.s3_bucket_arn
}

# S3 Event Notification: tự động gọi process-document khi có file mới
resource "aws_s3_bucket_notification" "documents_notification" {
  bucket = var.bucket_name

  lambda_function {
    lambda_function_arn = aws_lambda_function.process_document.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_s3_process]
}

# Lambda get-download-url (tạo Presigned URL tải file)
resource "aws_lambda_function" "get_download_url" {
  function_name = "${var.project_name}-get-download-url"
  role          = aws_iam_role.lambda_role.arn
  handler       = "get_download_url.lambda_handler"
  runtime       = "python3.9"
  timeout       = 10
  memory_size   = 128

  filename         = var.get_download_url_zip
  source_code_hash = filebase64sha256(var.get_download_url_zip)

  environment {
    variables = {
      LOCALSTACK_ENDPOINT = var.localstack_endpoint
      TABLE_NAME          = var.table_name
      BUCKET_NAME         = var.bucket_name
    }
  }

  tags = {
    Project     = var.project_name
    Function    = "get-download-url"
    Environment = "local"
  }
}
