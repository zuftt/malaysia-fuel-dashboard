# =============================================================================
# API Gateway HTTP — Replaces ALB, saves ~$17/mo
# Routes /api/* to ECS Fargate via VPC Link
# =============================================================================

# VPC Link — connects API Gateway to private resources in VPC
resource "aws_apigatewayv2_vpc_link" "ecs" {
  name               = "${var.project_name}-vpc-link"
  subnet_ids         = [aws_subnet.public_a.id, aws_subnet.public_b.id]
  security_group_ids = [aws_security_group.ecs.id]

  tags = { Name = "${var.project_name}-vpc-link" }
}

# Cloud Map namespace for service discovery
resource "aws_service_discovery_private_dns_namespace" "main" {
  name = "${var.project_name}.local"
  vpc  = aws_vpc.main.id
}

resource "aws_service_discovery_service" "api" {
  name = "api"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id

    dns_records {
      type = "A"
      ttl  = 10
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }
}

# HTTP API
resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["*"]
    max_age       = 3600
  }

  tags = { Name = "${var.project_name}-http-api" }
}

# Integration — forward to ECS via VPC Link
resource "aws_apigatewayv2_integration" "ecs" {
  api_id             = aws_apigatewayv2_api.main.id
  integration_type   = "HTTP_PROXY"
  integration_method = "ANY"
  integration_uri    = aws_service_discovery_service.api.arn
  connection_type    = "VPC_LINK"
  connection_id      = aws_apigatewayv2_vpc_link.ecs.id
}

# Catch-all route — proxy everything to ECS
resource "aws_apigatewayv2_route" "proxy" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.ecs.id}"
}

resource "aws_apigatewayv2_route" "root" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "ANY /"
  target    = "integrations/${aws_apigatewayv2_integration.ecs.id}"
}

# Default stage with auto-deploy
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gw.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      method         = "$context.httpMethod"
      path           = "$context.path"
      status         = "$context.status"
      latency        = "$context.responseLatency"
    })
  }
}

resource "aws_cloudwatch_log_group" "api_gw" {
  name              = "/aws/apigateway/${var.project_name}"
  retention_in_days = 7
}
