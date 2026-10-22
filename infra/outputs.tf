output "dashboard_url" {
  description = "HTTPS URL for the Northstar store operations dashboard."
  value       = "https://${aws_cloudfront_distribution.app.domain_name}/dashboard.html"
}

output "storefront_url" {
  description = "HTTPS URL for the Northstar Goods storefront."
  value       = "https://${aws_cloudfront_distribution.app.domain_name}/"
}

output "alb_dns_name" {
  description = "CloudFront-only application load balancer origin. Direct Internet requests receive 403."
  value       = aws_lb.app.dns_name
}

output "cognito_user_pool_id" {
  description = "Create user accounts in this Cognito user pool."
  value       = aws_cognito_user_pool.main.id
}

output "cognito_app_client_id" {
  description = "Public OAuth client identifier; it is safe to expose in the browser."
  value       = aws_cognito_user_pool_client.web.id
}

output "cognito_hosted_ui_domain" {
  description = "Cognito managed login domain."
  value       = "https://${aws_cognito_user_pool_domain.main.domain}.auth.${var.aws_region}.amazoncognito.com"
}

output "rds_endpoint" {
  description = "Private PostgreSQL endpoint, reachable only from application nodes."
  value       = aws_db_instance.main.address
}

output "cloudwatch_dashboard_name" {
  description = "CloudWatch operations dashboard name."
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

output "sns_alarm_topic_arn" {
  description = "Subscribe an operator to CloudWatch alarm notifications."
  value       = aws_sns_topic.alarms.arn
}
