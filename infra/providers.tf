terraform {
  required_version = ">= 1.8.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = var.project_name
      ManagedBy   = "Terraform"
      Environment = "production"
    }
  }
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}

data "aws_ec2_managed_prefix_list" "cloudfront_origin_facing" {
  name = "com.amazonaws.global.cloudfront.origin-facing"
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

data "archive_file" "application" {
  type        = "zip"
  source_dir  = "${path.module}/.."
  output_path = "${path.module}/northstar-app.zip"
  excludes = [
    "infra/**",
    ".github/**",
    ".qodo/**",
    ".git/**",
    ".gitignore",
    "README.md",
    "RESUME.md",
    "index.html",
    "backend/tests/**",
    "**/__pycache__/**",
    "**/*.pyc",
  ]
}

data "archive_file" "metrics_lambda" {
  type        = "zip"
  source_file = "${path.module}/../backend/lambda_metrics.py"
  output_path = "${path.module}/northstar-metrics-lambda.zip"
}
