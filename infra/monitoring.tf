# =============================================================================
# CloudWatch — Monitoring & Alarms
# =============================================================================

# Billing alarm — alert if costs exceed $25
resource "aws_cloudwatch_metric_alarm" "billing" {
  provider = aws.us_east_1

  alarm_name          = "${var.project_name}-billing-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 86400
  statistic           = "Maximum"
  threshold           = 25
  alarm_description   = "Alert when AWS charges exceed $25"
  treat_missing_data  = "notBreaching"

  dimensions = { Currency = "USD" }
}

# Lambda API errors
resource "aws_cloudwatch_metric_alarm" "api_errors" {
  alarm_name          = "${var.project_name}-api-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "API Lambda error rate too high"
  treat_missing_data  = "notBreaching"

  dimensions = { FunctionName = aws_lambda_function.api.function_name }
}

# Lambda API duration (cold start detection)
resource "aws_cloudwatch_metric_alarm" "api_duration" {
  alarm_name          = "${var.project_name}-api-slow"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Average"
  threshold           = 10000 # 10 seconds
  alarm_description   = "API Lambda average duration exceeds 10s"
  treat_missing_data  = "notBreaching"

  dimensions = { FunctionName = aws_lambda_function.api.function_name }
}

# Scraper Lambda failures
resource "aws_cloudwatch_metric_alarm" "scraper_errors" {
  alarm_name          = "${var.project_name}-scraper-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Scraper Lambda failed"
  treat_missing_data  = "notBreaching"

  dimensions = { FunctionName = aws_lambda_function.scraper.function_name }
}

# RDS CPU
resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "${var.project_name}-rds-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "RDS CPU above 80%"
  treat_missing_data  = "notBreaching"

  dimensions = { DBInstanceIdentifier = aws_db_instance.postgres.identifier }
}

# RDS free storage
resource "aws_cloudwatch_metric_alarm" "rds_storage" {
  alarm_name          = "${var.project_name}-rds-storage-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 2000000000 # 2GB
  alarm_description   = "RDS free storage below 2GB"
  treat_missing_data  = "notBreaching"

  dimensions = { DBInstanceIdentifier = aws_db_instance.postgres.identifier }
}
