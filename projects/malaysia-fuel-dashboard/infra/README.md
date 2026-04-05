# AWS Infrastructure — Malaysia Fuel Dashboard

## Architecture

```
CloudFront (CDN + HTTPS)
├── /           → S3 (Next.js static export)
├── /api/*      → API Gateway HTTP → ECS Fargate (FastAPI)
└── /health     → API Gateway HTTP → ECS Fargate
                                      ↓
                                  RDS PostgreSQL (private)
```

## Estimated Monthly Cost (~$28/mo)

| Service | Cost |
|---------|------|
| S3 + CloudFront | $2.00 |
| ECR | $0.50 |
| ECS Fargate (0.25 vCPU, 0.5GB) | $8.50 |
| API Gateway HTTP | $1.00 |
| RDS db.t3.micro | $13.50 |
| CloudWatch + Route 53 | $2.50 |
| **Total** | **~$28/mo** |

## Prerequisites

- AWS CLI configured (`aws configure`)
- Terraform >= 1.5.0
- Docker
- Node.js 20+

## First-Time Setup

### 1. Initialize Terraform

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

terraform init
terraform plan
terraform apply
```

### 2. Set sensitive variables

```bash
export TF_VAR_db_password="your-strong-password"
export TF_VAR_jwt_secret="your-random-secret"
terraform apply
```

### 3. Push Docker image

```bash
# Get ECR login
aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com

# Build & push
docker build -t fuel-dashboard-api .
docker tag fuel-dashboard-api:latest <ecr-url>:latest
docker push <ecr-url>:latest

# Force ECS to pull new image
aws ecs update-service --cluster fuel-dashboard-cluster --service fuel-dashboard-api --force-new-deployment
```

### 4. Deploy frontend

```bash
cd frontend
NEXT_PUBLIC_API_URL="" npm run build
aws s3 sync out/ s3://<bucket-name>/ --delete
aws cloudfront create-invalidation --distribution-id <dist-id> --paths "/*"
```

### 5. Configure GitHub Actions

Add these secrets to your GitHub repository:

| Secret | Value |
|--------|-------|
| `AWS_ROLE_ARN` | IAM role ARN for GitHub OIDC |
| `S3_BUCKET` | From `terraform output s3_bucket` |
| `CLOUDFRONT_DISTRIBUTION_ID` | From `terraform output cloudfront_distribution_id` |

## Useful Commands

```bash
# View outputs
terraform output

# Check ECS service status
aws ecs describe-services --cluster fuel-dashboard-cluster --services fuel-dashboard-api

# View container logs
aws logs tail /ecs/fuel-dashboard-api --follow

# Connect to RDS (from local via SSH tunnel or bastion)
psql -h <rds-endpoint> -U fueladmin -d fuel_dashboard
```

## Teardown

```bash
# Disable deletion protection on RDS first
aws rds modify-db-instance --db-instance-identifier fuel-dashboard-db --no-deletion-protection

terraform destroy
```
