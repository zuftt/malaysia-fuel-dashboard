# =============================================================================
# SNS — Price change notifications
# =============================================================================

resource "aws_sns_topic" "price_alerts" {
  name              = "${var.project_name}-price-alerts"
  kms_master_key_id = aws_kms_key.main.id

  tags = { Name = "${var.project_name}-price-alerts" }
}

# Email subscription (only if alert_email is provided)
resource "aws_sns_topic_subscription" "email" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.price_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# SNS topic policy
resource "aws_sns_topic_policy" "price_alerts" {
  arn = aws_sns_topic.price_alerts.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowLambdaPublish"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.lambda_scraper.arn
        }
        Action   = "SNS:Publish"
        Resource = aws_sns_topic.price_alerts.arn
      }
    ]
  })
}
