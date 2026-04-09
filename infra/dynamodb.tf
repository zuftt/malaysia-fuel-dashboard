# =============================================================================
# DynamoDB — Alert subscriptions & user preferences
# On-demand billing (pay per request) — essentially free at low traffic
# =============================================================================

resource "aws_dynamodb_table" "alert_subscriptions" {
  name         = "${var.project_name}-alert-subscriptions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "email"
  range_key    = "fuel_type"

  attribute {
    name = "email"
    type = "S"
  }

  attribute {
    name = "fuel_type"
    type = "S"
  }

  # KMS encryption with custom CMK
  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.main.arn
  }

  point_in_time_recovery {
    enabled = true
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = { Name = "${var.project_name}-alert-subscriptions" }
}
