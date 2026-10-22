resource "aws_lb" "app" {
  name                       = substr("${var.project_name}-alb", 0, 32)
  internal                   = false
  load_balancer_type         = "application"
  security_groups            = [aws_security_group.load_balancer.id]
  subnets                    = [for subnet in aws_subnet.public : subnet.id]
  drop_invalid_header_fields = true
  enable_deletion_protection = true
}

resource "aws_lb_target_group" "app" {
  name                 = substr("${var.project_name}-app", 0, 32)
  port                 = 8000
  protocol             = "HTTP"
  vpc_id               = aws_vpc.main.id
  target_type          = "instance"
  deregistration_delay = 30

  health_check {
    enabled             = true
    path                = "/api/health"
    matcher             = "200"
    interval            = 30
    timeout             = 10
    healthy_threshold   = 3
    unhealthy_threshold = 3
  }
}

resource "random_password" "cloudfront_origin_secret" {
  length  = 48
  special = false
}

resource "aws_lb_listener" "app" {
  load_balancer_arn = aws_lb.app.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "Forbidden"
      status_code  = "403"
    }
  }
}

resource "aws_lb_listener_rule" "cloudfront_only" {
  listener_arn = aws_lb_listener.app.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }

  condition {
    http_header {
      http_header_name = "X-Northstar-Origin-Verify"
      values           = [random_password.cloudfront_origin_secret.result]
    }
  }
}

resource "aws_launch_template" "app" {
  name_prefix            = "${var.project_name}-"
  image_id               = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  update_default_version = true
  depends_on             = [aws_secretsmanager_secret_version.order_webhook]
  user_data = base64encode(templatefile("${path.module}/user_data.sh.tftpl", {
    artifact_bucket          = aws_s3_bucket.artifacts.id
    artifact_key             = aws_s3_object.application.key
    aws_region               = var.aws_region
    bedrock_model_id         = var.bedrock_model_id
    db_host                  = aws_db_instance.main.address
    db_master_secret_arn     = aws_db_instance.main.master_user_secret[0].secret_arn
    db_app_secret_arn        = aws_secretsmanager_secret.application_db.arn
    order_webhook_secret_arn = aws_secretsmanager_secret.order_webhook.arn
    metrics_lambda_arn       = aws_lambda_function.metrics.arn
    project_name             = var.project_name
    cognito_user_pool_id     = aws_cognito_user_pool.main.id
    cognito_app_client_id    = aws_cognito_user_pool_client.web.id
    config_json = jsonencode({
      apiBaseUrl    = ""
      awsRegion     = var.aws_region
      userPoolId    = aws_cognito_user_pool.main.id
      appClientId   = aws_cognito_user_pool_client.web.id
      cognitoDomain = "https://${aws_cognito_user_pool_domain.main.domain}.auth.${var.aws_region}.amazoncognito.com"
      redirectUri   = "https://${aws_cloudfront_distribution.app.domain_name}/dashboard.html"
      sampleMode    = false
    })
    store_session_cookie_secure = "true"
  }))

  iam_instance_profile {
    name = aws_iam_instance_profile.app.name
  }

  vpc_security_group_ids = [aws_security_group.application.id]

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "enabled"
  }

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size           = 20
      volume_type           = "gp3"
      encrypted             = true
      delete_on_termination = true
    }
  }

  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.project_name}-app"
    }
  }
}

resource "aws_autoscaling_group" "app" {
  name                      = "${var.project_name}-app"
  min_size                  = 2
  max_size                  = 6
  desired_capacity          = 2
  vpc_zone_identifier       = [for subnet in aws_subnet.application : subnet.id]
  target_group_arns         = [aws_lb_target_group.app.arn]
  health_check_type         = "ELB"
  health_check_grace_period = 600
  default_instance_warmup   = 300
  wait_for_capacity_timeout = "20m"

  launch_template {
    id      = aws_launch_template.app.id
    version = aws_launch_template.app.latest_version
  }

  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 50
      instance_warmup        = 300
    }
  }
}

resource "aws_autoscaling_policy" "cpu" {
  name                   = "${var.project_name}-cpu-target"
  autoscaling_group_name = aws_autoscaling_group.app.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    target_value = 50
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
  }
}

resource "aws_cloudfront_distribution" "app" {
  enabled             = true
  comment             = "Northstar Commerce dashboard"
  web_acl_id          = aws_wafv2_web_acl.storefront.arn
  default_root_object = "index.html"
  price_class         = "PriceClass_100"
  http_version        = "http2and3"

  origin {
    domain_name = aws_lb.app.dns_name
    origin_id   = "northstar-application-alb"

    custom_header {
      name  = "X-Northstar-Origin-Verify"
      value = random_password.cloudfront_origin_secret.result
    }

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id         = "northstar-application-alb"
    viewer_protocol_policy   = "redirect-to-https"
    allowed_methods          = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods           = ["GET", "HEAD"]
    compress                 = true
    cache_policy_id          = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
    origin_request_policy_id = "b689b0a8-53d0-40ab-baf2-68738e2966ac"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
    minimum_protocol_version       = "TLSv1.2_2021"
  }

  depends_on = [aws_lb_listener_rule.cloudfront_only]
}
