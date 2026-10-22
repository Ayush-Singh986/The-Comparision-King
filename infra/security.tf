resource "aws_wafv2_web_acl" "storefront" {
  provider = aws.us_east_1
  name     = "${var.project_name}-edge-rate-limits"
  scope    = "CLOUDFRONT"

  default_action {
    allow {}
  }

  rule {
    name     = "limit-public-recommendation-requests"
    priority = 10

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 120
        aggregate_key_type = "IP"

        scope_down_statement {
          byte_match_statement {
            search_string         = "/api/store/recommendations"
            positional_constraint = "EXACTLY"

            field_to_match {
              uri_path {}
            }

            text_transformation {
              priority = 0
              type     = "NONE"
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "NorthstarPublicRecommendationLimit"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "NorthstarEdgeRateLimits"
    sampled_requests_enabled   = true
  }
}
