variable "aws_region" {
  description = "AWS region for the application and its data services."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Lowercase prefix for AWS resource names."
  type        = string
  default     = "northstar-commerce"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,25}$", var.project_name))
    error_message = "project_name must be 3-26 lowercase letters, digits, or hyphens and start with a letter."
  }
}

variable "bedrock_model_id" {
  description = "Amazon Bedrock model available to the account in the selected region."
  type        = string
  default     = "amazon.nova-lite-v1:0"
}

variable "instance_type" {
  description = "EC2 instance type for each application node."
  type        = string
  default     = "t3.small"
}

variable "database_instance_class" {
  description = "RDS PostgreSQL instance class."
  type        = string
  default     = "db.t4g.medium"
}

variable "alert_email" {
  description = "Optional email address for CloudWatch alarm notifications. Confirm the SNS subscription after deployment."
  type        = string
  default     = ""
}
