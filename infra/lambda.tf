# =============================================================================
# Lambda Functions — API + Scraper
# Container images from ECR, VPC-attached for RDS access
# =============================================================================

# ── CloudWatch Log Groups ──
resource "aws_cloudwatch_log_group" "api" {
  name              = "/aws/lambda/${var.project_name}-api"
  retention_in_days = 14
  kms_key_id        = aws_kms_key.main.arn

  tags = { Name = "${var.project_name}-api-logs" }
}

resource "aws_cloudwatch_log_group" "scraper" {
  name              = "/aws/lambda/${var.project_name}-scraper"
  retention_in_days = 14
  kms_key_id        = aws_kms_key.main.arn

  tags = { Name = "${var.project_name}-scraper-logs" }
}

# ── SSM Parameters for secrets ──
resource "aws_ssm_parameter" "database_url" {
  name   = "/${var.project_name}/DATABASE_URL"
  type   = "SecureString"
  key_id = aws_kms_key.main.id
  value  = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/fuel_dashboard"
}

resource "aws_ssm_parameter" "jwt_secret" {
  name   = "/${var.project_name}/JWT_SECRET"
  type   = "SecureString"
  key_id = aws_kms_key.main.id
  value  = var.jwt_secret
}

# ── API Lambda ──
resource "aws_lambda_function" "api" {
  function_name = "${var.project_name}-api"
  role          = aws_iam_role.lambda_api.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.api.repository_url}:latest"
  timeout       = 30
  memory_size   = 512

  vpc_config {
    subnet_ids         = [aws_subnet.private_a.id, aws_subnet.private_b.id]
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      ENVIRONMENT    = var.environment
      DATABASE_URL   = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/fuel_dashboard"
      SECRET_KEY     = var.jwt_secret
      DYNAMODB_TABLE = aws_dynamodb_table.alert_subscriptions.name
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.api,
    aws_db_instance.postgres,
  ]

  tags = { Name = "${var.project_name}-api" }
}

# ── Scraper Lambda ──
resource "aws_lambda_function" "scraper" {
  function_name = "${var.project_name}-scraper"
  role          = aws_iam_role.lambda_scraper.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.scraper.repository_url}:latest"
  timeout       = 120
  memory_size   = 256

  vpc_config {
    subnet_ids         = [aws_subnet.private_a.id, aws_subnet.private_b.id]
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      DATABASE_URL  = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/fuel_dashboard"
      SNS_TOPIC_ARN = aws_sns_topic.price_alerts.arn
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.scraper,
    aws_db_instance.postgres,
  ]

  tags = { Name = "${var.project_name}-scraper" }
}
