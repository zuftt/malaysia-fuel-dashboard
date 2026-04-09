# =============================================================================
# EventBridge — Scheduled trigger for price scraper
# Runs every Wednesday at 6PM MYT (10:00 UTC)
# =============================================================================

resource "aws_scheduler_schedule" "scraper" {
  name       = "${var.project_name}-weekly-scrape"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  # Every Wednesday at 6PM MYT (UTC+8)
  schedule_expression          = "cron(0 10 ? * WED *)"
  schedule_expression_timezone = "Asia/Kuala_Lumpur"

  target {
    arn      = aws_lambda_function.scraper.arn
    role_arn = aws_iam_role.scheduler.arn

    input = jsonencode({
      source = "eventbridge-schedule"
      action = "scrape_prices"
    })

    retry_policy {
      maximum_event_age_in_seconds = 3600
      maximum_retry_attempts       = 3
    }
  }
}

# IAM role for EventBridge Scheduler
resource "aws_iam_role" "scheduler" {
  name = "${var.project_name}-scheduler"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "scheduler.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "scheduler_invoke" {
  name = "${var.project_name}-scheduler-invoke"
  role = aws_iam_role.scheduler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "lambda:InvokeFunction"
      Resource = aws_lambda_function.scraper.arn
    }]
  })
}
