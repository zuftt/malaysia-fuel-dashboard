# =============================================================================
# CloudWatch Dashboard — Operational visibility
# =============================================================================

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-ops"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "API Lambda — Invocations & Errors"
          region  = var.aws_region
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", "${var.project_name}-api", { stat = "Sum", period = 300 }],
            ["AWS/Lambda", "Errors", "FunctionName", "${var.project_name}-api", { stat = "Sum", period = 300, color = "#d62728" }],
            ["AWS/Lambda", "Throttles", "FunctionName", "${var.project_name}-api", { stat = "Sum", period = 300, color = "#ff7f0e" }],
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "API Lambda — Duration (Cold Start Detection)"
          region  = var.aws_region
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", "${var.project_name}-api", { stat = "Average", period = 300 }],
            ["AWS/Lambda", "Duration", "FunctionName", "${var.project_name}-api", { stat = "Maximum", period = 300, color = "#d62728" }],
            ["AWS/Lambda", "Duration", "FunctionName", "${var.project_name}-api", { stat = "p99", period = 300, color = "#ff7f0e" }],
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "Scraper Lambda — Weekly Execution"
          region  = var.aws_region
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", "${var.project_name}-scraper", { stat = "Sum", period = 3600 }],
            ["AWS/Lambda", "Errors", "FunctionName", "${var.project_name}-scraper", { stat = "Sum", period = 3600, color = "#d62728" }],
            ["AWS/Lambda", "Duration", "FunctionName", "${var.project_name}-scraper", { stat = "Maximum", period = 3600, color = "#2ca02c" }],
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "RDS PostgreSQL — CPU & Connections"
          region  = var.aws_region
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", "${var.project_name}-db", { stat = "Average", period = 300 }],
            ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", "${var.project_name}-db", { stat = "Average", period = 300, yAxis = "right" }],
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6
        properties = {
          title   = "RDS — Storage & IOPS"
          region  = var.aws_region
          metrics = [
            ["AWS/RDS", "FreeStorageSpace", "DBInstanceIdentifier", "${var.project_name}-db", { stat = "Average", period = 300 }],
            ["AWS/RDS", "ReadIOPS", "DBInstanceIdentifier", "${var.project_name}-db", { stat = "Average", period = 300, yAxis = "right" }],
            ["AWS/RDS", "WriteIOPS", "DBInstanceIdentifier", "${var.project_name}-db", { stat = "Average", period = 300, yAxis = "right" }],
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 12
        width  = 12
        height = 6
        properties = {
          title   = "API Gateway — Requests & Latency"
          region  = var.aws_region
          metrics = [
            ["AWS/ApiGateway", "Count", "ApiId", aws_apigatewayv2_api.main.id, { stat = "Sum", period = 300 }],
            ["AWS/ApiGateway", "Latency", "ApiId", aws_apigatewayv2_api.main.id, { stat = "Average", period = 300, yAxis = "right" }],
            ["AWS/ApiGateway", "5xx", "ApiId", aws_apigatewayv2_api.main.id, { stat = "Sum", period = 300, color = "#d62728" }],
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 18
        width  = 12
        height = 6
        properties = {
          title   = "CloudFront — Requests & Error Rate"
          region  = "us-east-1"
          metrics = [
            ["AWS/CloudFront", "Requests", "DistributionId", aws_cloudfront_distribution.frontend.id, "Region", "Global", { stat = "Sum", period = 3600 }],
            ["AWS/CloudFront", "TotalErrorRate", "DistributionId", aws_cloudfront_distribution.frontend.id, "Region", "Global", { stat = "Average", period = 3600, color = "#d62728", yAxis = "right" }],
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 18
        width  = 12
        height = 6
        properties = {
          title   = "DynamoDB — Read/Write Capacity"
          region  = var.aws_region
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", aws_dynamodb_table.alert_subscriptions.name, { stat = "Sum", period = 300 }],
            ["AWS/DynamoDB", "ConsumedWriteCapacityUnits", "TableName", aws_dynamodb_table.alert_subscriptions.name, { stat = "Sum", period = 300, yAxis = "right" }],
          ]
          view = "timeSeries"
        }
      },
    ]
  })
}
