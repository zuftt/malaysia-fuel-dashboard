variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-1" # Singapore — closest to Malaysia
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

variable "container_cpu" {
  description = "Fargate task CPU units (256 = 0.25 vCPU)"
  type        = number
  default     = 256
}

variable "container_memory" {
  description = "Fargate task memory in MB"
  type        = number
  default     = 512
}

variable "domain_name" {
  description = "Custom domain name (optional, leave empty to skip)"
  type        = string
  default     = ""
}
