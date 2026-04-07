# AWS Infrastructure — Malaysia Fuel Dashboard (Serverless)

## Architecture

```
CloudFront (CDN + HTTPS)
├── /*        → S3 (Next.js static export, versioned, KMS encrypted)
├── /api/*    → API Gateway HTTP → Lambda (FastAPI + Mangum)
└── /health   → API Gateway HTTP → Lambda
                                    ↓
                              RDS PostgreSQL (private subnet, KMS encrypted)

EventBridge (Wed 6PM MYT) → Scraper Lambda → RDS + SNS (price alerts)

DynamoDB (alert subscriptions) ← API Lambda (read/write)
```

## Estimated Monthly Cost (~$17/mo)

| Service | Cost |
|---------|------|
| S3 + CloudFront | $2.00 |
| ECR (2 repos) | $0.50 |
| Lambda (API + Scraper) | $0.50 |
| API Gateway HTTP | $0.50 |
| RDS db.t3.micro | $13.50 |
| DynamoDB (on-demand) | $0.00 |
| SNS + EventBridge | $0.00 |
| CloudWatch | $0.50 |
| KMS | $1.00 |
| CloudTrail | $0.00 |
| VPC Endpoints (SNS) | ~$7.00 |
| **Total** | **~$17/mo** |

*Note: VPC endpoint for SNS adds ~$7/mo. Remove if you don't need SNS from within VPC.*

## AWS Services Used

| Category | Services |
|----------|----------|
| **Compute** | Lambda (API + Scraper), ECR |
| **Networking** | VPC, Public/Private Subnets, VPC Endpoints, CloudFront |
| **Storage** | S3 (versioned + lifecycle), ECR |
| **Database** | RDS PostgreSQL, DynamoDB |
| **Security** | IAM (least-privilege), KMS CMK, CloudTrail, GitHub OIDC |
| **Integration** | API Gateway HTTP, EventBridge, SNS |
| **Monitoring** | CloudWatch (Alarms + Logs) |
| **CI/CD** | GitHub Actions (OIDC — no static keys) |

## Setup

### 1. Prerequisites

```bash
brew install awscli terraform
aws configure  # Access Key from IAM
```

### 2. Deploy Infrastructure

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars

export TF_VAR_db_password="$(openssl rand -base64 24)"
export TF_VAR_jwt_secret="$(openssl rand -base64 32)"

terraform init
terraform plan
terraform apply
```

### 3. Push Lambda Images

```bash
ECR_API=$(terraform output -raw ecr_api_url)
ECR_SCRAPER=$(terraform output -raw ecr_scraper_url)

aws ecr get-login-password --region ap-southeast-1 | \
  docker login --username AWS --password-stdin $ECR_API

# API
docker build -t fuel-api -f Dockerfile .
docker tag fuel-api:latest $ECR_API:latest
docker push $ECR_API:latest
aws lambda update-function-code --function-name fuel-dashboard-api --image-uri $ECR_API:latest

# Scraper
docker build -t fuel-scraper -f Dockerfile.scraper .
docker tag fuel-scraper:latest $ECR_SCRAPER:latest
docker push $ECR_SCRAPER:latest
aws lambda update-function-code --function-name fuel-dashboard-scraper --image-uri $ECR_SCRAPER:latest
```

### 4. Deploy Frontend

```bash
S3_BUCKET=$(terraform output -raw s3_bucket)
CF_DIST=$(terraform output -raw cloudfront_distribution_id)

cd ../frontend
NEXT_PUBLIC_API_URL="" npm run build
aws s3 sync out/ s3://$S3_BUCKET/ --delete
aws cloudfront create-invalidation --distribution-id $CF_DIST --paths "/*"
```

### 5. Configure GitHub Actions

Add one secret: `AWS_ROLE_ARN` (from `terraform output github_actions_role_arn`).
Add: `S3_BUCKET`, `CLOUDFRONT_DISTRIBUTION_ID` from outputs.

CI/CD uses OIDC — no static AWS keys needed.

## Skills Demonstrated

- **Serverless**: Lambda, API Gateway, EventBridge, SNS, DynamoDB
- **IaC**: Terraform (12 config files)
- **Networking**: VPC, public/private subnets, VPC endpoints, security groups
- **Security**: IAM least-privilege, KMS CMK, CloudTrail, GitHub OIDC
- **CI/CD**: GitHub Actions with OIDC (keyless)
- **Containers**: Docker, ECR (Lambda container images)
- **Databases**: RDS PostgreSQL, DynamoDB
- **Monitoring**: CloudWatch alarms + structured logging
- **Storage**: S3 versioning, lifecycle policies, encryption
