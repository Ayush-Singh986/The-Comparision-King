resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db"
  subnet_ids = [for subnet in aws_subnet.database : subnet.id]
}

resource "aws_db_instance" "main" {
  depends_on                            = [aws_cloudwatch_log_group.database]
  identifier                            = var.project_name
  engine                                = "postgres"
  engine_version                        = "16"
  instance_class                        = var.database_instance_class
  allocated_storage                     = 20
  max_allocated_storage                 = 50
  storage_type                          = "gp3"
  storage_encrypted                     = true
  db_name                               = "northstar"
  username                              = "northstar_master"
  manage_master_user_password           = true
  db_subnet_group_name                  = aws_db_subnet_group.main.name
  vpc_security_group_ids                = [aws_security_group.database.id]
  multi_az                              = var.high_availability
  publicly_accessible                   = false
  backup_retention_period               = 7
  backup_window                         = "03:00-04:00"
  maintenance_window                    = "sun:04:00-sun:05:00"
  auto_minor_version_upgrade            = true
  deletion_protection                   = true
  skip_final_snapshot                   = false
  final_snapshot_identifier             = "${var.project_name}-final"
  copy_tags_to_snapshot                 = true
  performance_insights_enabled          = var.enable_performance_insights
  performance_insights_retention_period = var.enable_performance_insights ? 7 : null
  monitoring_interval                   = 0
  enabled_cloudwatch_logs_exports       = ["postgresql", "upgrade"]
}

resource "aws_cloudwatch_log_group" "database" {
  for_each          = toset(["postgresql", "upgrade"])
  name              = "/aws/rds/instance/${var.project_name}/${each.value}"
  retention_in_days = 30
}

resource "random_password" "application_db" {
  length           = 48
  special          = false
  override_special = ""
}

resource "aws_secretsmanager_secret" "application_db" {
  name                    = "${var.project_name}/application-database"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "application_db" {
  secret_id = aws_secretsmanager_secret.application_db.id
  secret_string = jsonencode({
    username = "northstar_app"
    password = random_password.application_db.result
  })
}

resource "random_password" "order_webhook" {
  length           = 64
  special          = false
  override_special = ""
}

resource "aws_secretsmanager_secret" "order_webhook" {
  name                    = "${var.project_name}/order-webhook"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "order_webhook" {
  secret_id = aws_secretsmanager_secret.order_webhook.id
  secret_string = jsonencode({
    webhook_secret = random_password.order_webhook.result
  })
}

resource "aws_s3_bucket" "artifacts" {
  bucket        = "${var.project_name}-${data.aws_caller_identity.current.account_id}-${random_id.suffix.hex}"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket                  = aws_s3_bucket.artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_object" "application" {
  bucket       = aws_s3_bucket.artifacts.id
  key          = "releases/${data.archive_file.application.output_sha256}.zip"
  source       = data.archive_file.application.output_path
  source_hash  = data.archive_file.application.output_sha256
  content_type = "application/zip"
}

resource "aws_s3_bucket_lifecycle_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    id     = "expire-old-release-artifacts"
    status = "Enabled"

    filter {
      prefix = "releases/"
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }

    expiration {
      days = 90
    }
  }
}

resource "random_id" "suffix" {
  byte_length = 4
}
