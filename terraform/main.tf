terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region     = var.aws_region
  access_key = "test"
  secret_key = "test"

  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  endpoints {
    s3           = var.localstack_endpoint
    dynamodb     = var.localstack_endpoint
    iam          = var.localstack_endpoint
    lambda       = var.localstack_endpoint
    sts          = var.localstack_endpoint
    logs         = var.localstack_endpoint
    cloudwatch   = var.localstack_endpoint
    apigateway   = var.localstack_endpoint
    cloudfront   = var.localstack_endpoint
  }
}

# Module 1: Lưu trữ (S3 + DynamoDB + CloudFront CDN)
module "storage" {
  source      = "./modules/storage"
  bucket_name = var.bucket_name
  table_name  = var.table_name
}

# Module 2: Lambda functions + IAM
module "lambda" {
  source = "./modules/lambda"

  project_name        = var.project_name
  localstack_endpoint = var.localstack_endpoint_docker
  bucket_name         = var.bucket_name
  s3_bucket_arn       = module.storage.bucket_arn
  table_name          = var.table_name
  dynamodb_table_arn  = module.storage.table_arn

  list_documents_zip    = "../lambda/list_documents.zip"
  upload_document_zip   = "../lambda/upload_document.zip"
  process_document_zip  = "../lambda/process_document.zip"
  delete_document_zip   = "../lambda/delete_document.zip"
  get_download_url_zip  = "../lambda/get_download_url.zip"

  depends_on = [module.storage]
}

# Module 3: API Gateway (REST API)
module "api_gateway" {
  source = "./modules/api_gateway"

  project_name = var.project_name
  stage_name   = var.stage_name

  list_documents_invoke_arn  = module.lambda.list_documents_invoke_arn
  list_documents_name        = module.lambda.list_documents_name
  upload_document_invoke_arn = module.lambda.upload_document_invoke_arn
  upload_document_name       = module.lambda.upload_document_name
  delete_document_invoke_arn = module.lambda.delete_document_invoke_arn
  delete_document_name       = module.lambda.delete_document_name
  get_download_url_invoke_arn = module.lambda.get_download_url_invoke_arn
  get_download_url_name       = module.lambda.get_download_url_name

  depends_on = [module.lambda]
}
