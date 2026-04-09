# =============================================================================
# ECR — Container registries for Lambda images (~$0.50/mo)
# =============================================================================

# API Lambda image
resource "aws_ecr_repository" "api" {
  name                 = "${var.project_name}-api"
  image_tag_mutability = "MUTABLE"
  force_delete         = false

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = { Name = "${var.project_name}-api" }
}

# Scraper Lambda image
resource "aws_ecr_repository" "scraper" {
  name                 = "${var.project_name}-scraper"
  image_tag_mutability = "MUTABLE"
  force_delete         = false

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = { Name = "${var.project_name}-scraper" }
}

# Lifecycle — keep last 5 images each
resource "aws_ecr_lifecycle_policy" "api" {
  repository = aws_ecr_repository.api.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 5 images"
      selection     = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = 5 }
      action        = { type = "expire" }
    }]
  })
}

resource "aws_ecr_lifecycle_policy" "scraper" {
  repository = aws_ecr_repository.scraper.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 5 images"
      selection     = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = 5 }
      action        = { type = "expire" }
    }]
  })
}
