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
  description = "Cost-conscious RDS PostgreSQL instance class for the portfolio deployment."
  type        = string
  default     = "db.t4g.micro"
}

variable "high_availability" {
  description = "Enable multi-AZ RDS, two baseline EC2 instances, and one NAT Gateway per AZ. This increases monthly cost."
  type        = bool
  default     = false
}

variable "enable_performance_insights" {
  description = "Enable RDS Performance Insights, which may add cost depending on AWS pricing."
  type        = bool
  default     = false
}

variable "monthly_budget_limit_usd" {
  description = "Monthly AWS cost-alert threshold in USD. Configure alert_email to receive notifications."
  type        = number
  default     = 50
  validation {
    condition     = var.monthly_budget_limit_usd > 0
    error_message = "monthly_budget_limit_usd must be greater than zero."
  }
}

variable "origin_domain_name" {
  description = "Optional DNS name that resolves to the ALB and matches its ACM origin certificate. Both origin TLS variables must be set together."
  type        = string
  default     = ""
}

variable "origin_certificate_arn" {
  description = "Optional ACM certificate ARN in the ALB region for origin_domain_name."
  type        = string
  default     = ""
  validation {
    condition = (
      (var.origin_domain_name == "" && var.origin_certificate_arn == "")
      || (var.origin_domain_name != "" && var.origin_certificate_arn != "")
    )
    error_message = "Set both origin_domain_name and origin_certificate_arn to enable HTTPS from CloudFront to the ALB."
  }
}

variable "alert_email" {
  description = "Optional email address for CloudWatch alarm notifications. Confirm the SNS subscription after deployment."
  type        = string
  default     = ""
}
