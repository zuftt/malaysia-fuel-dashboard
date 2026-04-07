# =============================================================================
# RDS PostgreSQL — db.t3.micro, private subnets, KMS encrypted (~$13.50/mo)
# =============================================================================

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  tags       = { Name = "${var.project_name}-db-subnet" }
}

resource "aws_db_instance" "postgres" {
  identifier = "${var.project_name}-db"

  engine         = "postgres"
  engine_version = "16.4"
  instance_class = "db.t3.micro"

  allocated_storage     = 20
  max_allocated_storage = 50
  storage_type          = "gp3"

  # KMS encryption with custom CMK
  storage_encrypted = true
  kms_key_id        = aws_kms_key.main.arn

  db_name  = "fuel_dashboard"
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  skip_final_snapshot       = false
  final_snapshot_identifier = "${var.project_name}-final-snapshot"
  deletion_protection       = true

  performance_insights_enabled = false

  # Multi-AZ for resilience (automatic failover)
  # Set to false to save ~$13/mo during development
  multi_az = true

  tags = { Name = "${var.project_name}-postgres" }
}
