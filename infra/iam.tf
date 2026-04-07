# =============================================================================
# IAM — Least-privilege roles for Lambda + GitHub OIDC
# =============================================================================

# ── API Lambda Role ──
resource "aws_iam_role" "lambda_api" {
  name = "${var.project_name}-lambda-api"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# API Lambda: VPC access (ENI management for private subnets)
resource "aws_iam_role_policy" "lambda_api_vpc" {
  name = "vpc-access"
  role = aws_iam_role.lambda_api.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ec2:CreateNetworkInterface",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DeleteNetworkInterface",
        "ec2:AssignPrivateIpAddresses",
        "ec2:UnassignPrivateIpAddresses"
      ]
      Resource = "*"
    }]
  })
}

# API Lambda: CloudWatch logs (scoped to its own log group)
resource "aws_iam_role_policy" "lambda_api_logs" {
  name = "cloudwatch-logs"
  role = aws_iam_role.lambda_api.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ]
      Resource = "${aws_cloudwatch_log_group.api.arn}:*"
    }]
  })
}

# API Lambda: Read SSM parameters (scoped to project prefix)
resource "aws_iam_role_policy" "lambda_api_ssm" {
  name = "ssm-read"
  role = aws_iam_role.lambda_api.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/${var.project_name}/*"
      },
      {
        Effect   = "Allow"
        Action   = "kms:Decrypt"
        Resource = aws_kms_key.main.arn
      }
    ]
  })
}

# API Lambda: DynamoDB access (scoped to alert table)
resource "aws_iam_role_policy" "lambda_api_dynamodb" {
  name = "dynamodb-access"
  role = aws_iam_role.lambda_api.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ]
      Resource = aws_dynamodb_table.alert_subscriptions.arn
    }]
  })
}

# ── Scraper Lambda Role ──
resource "aws_iam_role" "lambda_scraper" {
  name = "${var.project_name}-lambda-scraper"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# Scraper Lambda: VPC access
resource "aws_iam_role_policy" "lambda_scraper_vpc" {
  name = "vpc-access"
  role = aws_iam_role.lambda_scraper.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ec2:CreateNetworkInterface",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DeleteNetworkInterface",
        "ec2:AssignPrivateIpAddresses",
        "ec2:UnassignPrivateIpAddresses"
      ]
      Resource = "*"
    }]
  })
}

# Scraper Lambda: CloudWatch logs (scoped)
resource "aws_iam_role_policy" "lambda_scraper_logs" {
  name = "cloudwatch-logs"
  role = aws_iam_role.lambda_scraper.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ]
      Resource = "${aws_cloudwatch_log_group.scraper.arn}:*"
    }]
  })
}

# Scraper Lambda: Publish to SNS (scoped to price alerts topic)
resource "aws_iam_role_policy" "lambda_scraper_sns" {
  name = "sns-publish"
  role = aws_iam_role.lambda_scraper.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "sns:Publish"
        Resource = aws_sns_topic.price_alerts.arn
      },
      {
        Effect   = "Allow"
        Action   = "kms:GenerateDataKey*"
        Resource = aws_kms_key.main.arn
      }
    ]
  })
}

# =============================================================================
# GitHub OIDC — Keyless CI/CD (no static AWS credentials)
# =============================================================================

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["ffffffffffffffffffffffffffffffffffffffff"]

  tags = { Name = "${var.project_name}-github-oidc" }
}

resource "aws_iam_role" "github_actions" {
  name = "${var.project_name}-github-actions"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.github.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:${var.github_org}/${var.github_repo}:*"
        }
      }
    }]
  })
}

# GitHub Actions: Push to ECR (scoped to project repos)
resource "aws_iam_role_policy" "github_ecr" {
  name = "ecr-push"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "ecr:GetAuthorizationToken"
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload"
        ]
        Resource = [
          aws_ecr_repository.api.arn,
          aws_ecr_repository.scraper.arn
        ]
      }
    ]
  })
}

# GitHub Actions: Update Lambda functions
resource "aws_iam_role_policy" "github_lambda" {
  name = "lambda-deploy"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "lambda:UpdateFunctionCode",
        "lambda:GetFunction"
      ]
      Resource = [
        aws_lambda_function.api.arn,
        aws_lambda_function.scraper.arn
      ]
    }]
  })
}

# GitHub Actions: Deploy frontend to S3 + invalidate CloudFront
resource "aws_iam_role_policy" "github_frontend" {
  name = "frontend-deploy"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.frontend.arn,
          "${aws_s3_bucket.frontend.arn}/*"
        ]
      },
      {
        Effect   = "Allow"
        Action   = "cloudfront:CreateInvalidation"
        Resource = aws_cloudfront_distribution.frontend.arn
      }
    ]
  })
}
