resource "aws_lambda_function" "metrics" {
  function_name    = "${var.project_name}-event-metrics"
  description      = "Publishes accepted customer events as CloudWatch custom metrics."
  role             = aws_iam_role.metrics_lambda.arn
  runtime          = "python3.12"
  handler          = "lambda_metrics.handler"
  filename         = data.archive_file.metrics_lambda.output_path
  source_code_hash = data.archive_file.metrics_lambda.output_base64sha256
  timeout          = 10
  memory_size      = 128

  environment {
    variables = {
      METRIC_NAMESPACE = "${var.project_name}/Commerce"
    }
  }
}

resource "aws_cloudwatch_log_group" "metrics_lambda" {
  name              = "/aws/lambda/${aws_lambda_function.metrics.function_name}"
  retention_in_days = 30
}

resource "aws_sns_topic" "alarms" {
  name = "${var.project_name}-alarms"
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.alert_email == "" ? 0 : 1
  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

resource "aws_cloudwatch_metric_alarm" "alb_target_errors" {
  alarm_name          = "${var.project_name}-target-5xx"
  alarm_description   = "Application targets returned repeated 5xx responses."
  namespace           = "AWS/ApplicationELB"
  metric_name         = "HTTPCode_Target_5XX_Count"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 2
  threshold           = 10
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  dimensions = {
    LoadBalancer = aws_lb.app.arn_suffix
    TargetGroup  = aws_lb_target_group.app.arn_suffix
  }
  alarm_actions = [aws_sns_topic.alarms.arn]
}

resource "aws_cloudwatch_metric_alarm" "alb_latency" {
  alarm_name          = "${var.project_name}-alb-latency"
  alarm_description   = "Average application target response time exceeded 1.5 seconds."
  namespace           = "AWS/ApplicationELB"
  metric_name         = "TargetResponseTime"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 3
  threshold           = 1.5
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  dimensions = {
    LoadBalancer = aws_lb.app.arn_suffix
    TargetGroup  = aws_lb_target_group.app.arn_suffix
  }
  alarm_actions = [aws_sns_topic.alarms.arn]
}

resource "aws_cloudwatch_metric_alarm" "database_cpu" {
  alarm_name          = "${var.project_name}-database-cpu"
  alarm_description   = "RDS CPU utilization stayed above 80 percent."
  namespace           = "AWS/RDS"
  metric_name         = "CPUUtilization"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 3
  threshold           = 80
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.identifier
  }
  alarm_actions = [aws_sns_topic.alarms.arn]
}

resource "aws_cloudwatch_metric_alarm" "low_recommendation_ctr" {
  alarm_name          = "${var.project_name}-recommendation-ctr-low"
  alarm_description   = "Recommendation clicks fell below 3% after at least 20 impressions per 15-minute interval."
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  threshold           = 3
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alarms.arn]

  metric_query {
    id          = "clicks"
    return_data = false
    metric {
      metric_name = "CustomerEvents"
      namespace   = "${var.project_name}/Commerce"
      period      = 900
      stat        = "Sum"
      dimensions = {
        EventType = "recommendation_click"
      }
    }
  }

  metric_query {
    id          = "impressions"
    return_data = false
    metric {
      metric_name = "CustomerEvents"
      namespace   = "${var.project_name}/Commerce"
      period      = 900
      stat        = "Sum"
      dimensions = {
        EventType = "recommendation_impression"
      }
    }
  }

  metric_query {
    id          = "ctr"
    expression  = "IF(impressions >= 20, 100 * clicks / impressions, 100)"
    label       = "Recommendation click-through rate (%)"
    return_data = true
  }
}

resource "aws_cloudwatch_metric_alarm" "unusual_camera_interest" {
  alarm_name          = "${var.project_name}-unusual-camera-interest"
  alarm_description   = "Hourly camera product views deviated from the recent expected range."
  comparison_operator = "LessThanLowerOrGreaterThanUpperThreshold"
  evaluation_periods  = 2
  threshold_metric_id = "band"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alarms.arn]

  metric_query {
    id          = "views"
    return_data = false
    metric {
      metric_name = "ProductViews"
      namespace   = "${var.project_name}/Commerce"
      period      = 3600
      stat        = "Sum"
      dimensions = {
        ProductId = "camera-x2"
      }
    }
  }

  metric_query {
    id          = "band"
    expression  = "ANOMALY_DETECTION_BAND(views, 2)"
    label       = "Expected product-view range"
    return_data = true
  }
}

resource "aws_cloudwatch_metric_alarm" "metrics_lambda_errors" {
  alarm_name          = "${var.project_name}-metrics-lambda-errors"
  alarm_description   = "The asynchronous event-metrics Lambda reported errors."
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 2
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  dimensions = {
    FunctionName = aws_lambda_function.metrics.function_name
  }
  alarm_actions = [aws_sns_topic.alarms.arn]
}

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-operations"
  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric", x = 0, y = 0, width = 12, height = 6,
        properties = {
          title  = "Customer events by type"
          view   = "timeSeries"
          region = var.aws_region
          period = 300
          stat   = "Sum"
          metrics = [
            for event_type in ["product_view", "search", "purchase", "recommendation_impression", "recommendation_click"] :
            ["${var.project_name}/Commerce", "CustomerEvents", "EventType", event_type]
          ]
        }
      },
      {
        type = "metric", x = 12, y = 0, width = 12, height = 6,
        properties = {
          title  = "Application target latency and errors"
          view   = "timeSeries"
          region = var.aws_region
          period = 300
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", aws_lb.app.arn_suffix, "TargetGroup", aws_lb_target_group.app.arn_suffix],
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer", aws_lb.app.arn_suffix, "TargetGroup", aws_lb_target_group.app.arn_suffix, { yAxis = "right", stat = "Sum" }]
          ]
        }
      },
      {
        type = "metric", x = 0, y = 6, width = 12, height = 6,
        properties = {
          title  = "Database CPU"
          view   = "timeSeries"
          region = var.aws_region
          period = 300
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", aws_db_instance.main.identifier]
          ]
        }
      }
    ]
  })
}
