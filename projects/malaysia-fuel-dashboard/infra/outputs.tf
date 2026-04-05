output "cloudfront_url" {
  description = "Frontend URL (CloudFront)"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "api_gateway_url" {
  description = "API Gateway endpoint"
  value       = aws_apigatewayv2_api.main.api_endpoint
}

output "ecr_repository_url" {
  description = "ECR repository URL for Docker push"
  value       = aws_ecr_repository.api.repository_url
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}

output "s3_bucket" {
  description = "S3 bucket for frontend deployment"
  value       = aws_s3_bucket.frontend.bucket
}

output "ecs_cluster" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service" {
  description = "ECS service name"
  value       = aws_ecs_service.api.name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (for cache invalidation)"
  value       = aws_cloudfront_distribution.frontend.id
}
