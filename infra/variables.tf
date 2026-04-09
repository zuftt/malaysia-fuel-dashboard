variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "fuel-dashboard"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "prod"
}

variable "db_username" {
  description = "RDS master username"
  type        = string
  default     = "fueladmin"
  sensitive   = true
}

variable "db_password" {
  description = "RDS master password"
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "JWT signing secret"
  type        = string
  sensitive   = true
}

variable "github_org" {
  description = "GitHub org/user for OIDC trust"
  type        = string
  default     = "zuftt"
}

variable "github_repo" {
  description = "GitHub repo name for OIDC trust"
  type        = string
  default     = "malaysia-fuel-dashboard"
}

variable "alert_email" {
  description = "Email for price change SNS notifications"
  type        = string
  default     = ""
}
