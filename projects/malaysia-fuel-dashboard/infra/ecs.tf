# =============================================================================
# ECS Fargate — 0.25 vCPU, 0.5GB RAM (~$8.50/mo)
# Public subnet, no NAT Gateway needed
# =============================================================================

resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "disabled" # Save cost — enable when debugging
  }

  tags = { Name = "${var.project_name}-cluster" }
}

# CloudWatch log group for container logs
resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${var.project_name}-api"
  retention_in_days = 14

  tags = { Name = "${var.project_name}-api-logs" }
}

# SSM Parameters for secrets
resource "aws_ssm_parameter" "database_url" {
  name  = "/${var.project_name}/DATABASE_URL"
  type  = "SecureString"
  value = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/fuel_dashboard"
}

resource "aws_ssm_parameter" "jwt_secret" {
  name  = "/${var.project_name}/JWT_SECRET"
  type  = "SecureString"
  value = var.jwt_secret
}

# Task Definition
resource "aws_ecs_task_definition" "api" {
  family                   = "${var.project_name}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.container_cpu
  memory                   = var.container_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "api"
      image = "${aws_ecr_repository.api.repository_url}:latest"

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "ENVIRONMENT", value = var.environment },
        { name = "PORT", value = "8000" },
        { name = "CORS_ORIGINS", value = "https://${aws_cloudfront_distribution.frontend.domain_name},http://localhost:3000" },
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = aws_ssm_parameter.database_url.arn
        },
        {
          name      = "SECRET_KEY"
          valueFrom = aws_ssm_parameter.jwt_secret.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.api.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "api"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/health')\" || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = { Name = "${var.project_name}-api-task" }
}

# ECS Service
resource "aws_ecs_service" "api" {
  name            = "${var.project_name}-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.public_a.id, aws_subnet.public_b.id]
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true # Public subnet — no NAT Gateway needed
  }

  # Allow new deployments to drain gracefully
  deployment_minimum_healthy_percent = 0
  deployment_maximum_percent         = 200

  tags = { Name = "${var.project_name}-api-service" }

  depends_on = [aws_db_instance.postgres]
}
