output "cloudfront_url" {
  description = "Frontend URL"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "api_gateway_url" {
  description = "API Gateway endpoint"
  value       = aws_apigatewayv2_api.main.api_endpoint
}

output "ecr_api_url" {
  description = "ECR repository URL for API Lambda image"
  value       = aws_ecr_repository.api.repository_url
}

output "ecr_scraper_url" {
  description = "ECR repository URL for Scraper Lambda image"
  value       = aws_ecr_repository.scraper.repository_url
}

output "s3_bucket" {
  description = "S3 bucket for frontend"
  value       = aws_s3_bucket.frontend.bucket
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.frontend.id
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}

output "github_actions_role_arn" {
  description = "IAM role ARN for GitHub Actions OIDC"
  value       = aws_iam_role.github_actions.arn
}

output "sns_topic_arn" {
  description = "SNS topic for price alerts"
  value       = aws_sns_topic.price_alerts.arn
}

output "dynamodb_table" {
  description = "DynamoDB alert subscriptions table"
  value       = aws_dynamodb_table.alert_subscriptions.name
}

output "kms_key_id" {
  description = "KMS CMK ID"
  value       = aws_kms_key.main.key_id
}
