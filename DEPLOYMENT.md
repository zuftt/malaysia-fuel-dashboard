# Deployment (AWS)

Production runs **serverless on AWS**: Terraform provisions VPC, RDS, Lambda (container images on ECR), API Gateway HTTP, S3, CloudFront, EventBridge, SNS, DynamoDB, and related IAM/KMS/CloudWatch resources. Details and cost notes live in [infra/README.md](infra/README.md).

## Prerequisites

- [AWS CLI](https://aws.amazon.com/cli/) configured (`aws configure` or SSO profile)
- [Terraform](https://www.terraform.io/) ≥ 1.5
- [Docker](https://docs.docker.com/get-docker/) with **Buildx** (included with Docker Desktop) for Lambda images pushed to ECR
- [uv](https://docs.astral.sh/uv/) (optional — used by [awslabs/mcp](https://github.com/awslabs/mcp) servers in [.cursor/mcp.json](.cursor/mcp.json) for docs + IaC assistance in Cursor)

## One-time: provision infrastructure

From the repo root:

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars: aws_region, github_org, github_repo, alert_email, etc.

# Use hex for DB password — RDS rejects many base64 strings (/, @, ", space).
export TF_VAR_db_password="$(openssl rand -hex 20)"
export TF_VAR_jwt_secret="$(openssl rand -hex 32)"

terraform init
terraform plan
terraform apply
```

Capture outputs for later steps and for GitHub Actions:

```bash
terraform output -raw github_actions_role_arn
terraform output -raw s3_bucket
terraform output -raw cloudfront_distribution_id
terraform output cloudfront_url
```

Lambda function names follow `project_name` (default **`fuel-dashboard-api`** and **`fuel-dashboard-scraper`**).

## First deploy: container images + static site

After `terraform apply`, ECR repos exist but Lambdas need images, and S3 needs the Next.js static export.

Run `terraform output` commands from `infra/`. Use the same `aws_region` as in `terraform.tfvars` (below: `ap-southeast-1`).

```bash
cd infra
ECR_API=$(terraform output -raw ecr_api_url | tr -d '\n\r')
ECR_SCRAPER=$(terraform output -raw ecr_scraper_url | tr -d '\n\r')
REGION="ap-southeast-1"

aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$(echo "$ECR_API" | cut -d/ -f1)"

cd ..   # repository root — Dockerfiles are here

# Lambda needs linux/amd64 and a plain Docker manifest (no OCI attestations).
docker buildx build --platform linux/amd64 --provenance=false --sbom=false --push \
  -t "${ECR_API}:latest" -f Dockerfile .
docker buildx build --platform linux/amd64 --provenance=false --sbom=false --push \
  -t "${ECR_SCRAPER}:latest" -f Dockerfile.scraper .

# If Lambdas already exist, refresh code (optional after first terraform apply):
aws lambda update-function-code --function-name fuel-dashboard-api --image-uri "${ECR_API}:latest" --region "$REGION"
aws lambda update-function-code --function-name fuel-dashboard-scraper --image-uri "${ECR_SCRAPER}:latest" --region "$REGION"
```

Frontend (relative URLs to CloudFront `/api/*`; leave `NEXT_PUBLIC_API_URL` empty for production):

```bash
cd infra
S3_BUCKET=$(terraform output -raw s3_bucket | tr -d '\n\r')
CF_DIST=$(terraform output -raw cloudfront_distribution_id | tr -d '\n\r')
REGION="ap-southeast-1"   # match terraform.tfvars
cd ../frontend
NEXT_PUBLIC_API_URL="" npm run build
aws s3 sync out/ "s3://$S3_BUCKET/" --delete --region "$REGION"
aws cloudfront create-invalidation --distribution-id "$CF_DIST" --paths "/*"
```

## CI/CD (GitHub Actions)

Workflow: [.github/workflows/deploy.yml](.github/workflows/deploy.yml) (triggers on push to **`main`**).

Repository secrets (typical):

| Secret | Source |
|--------|--------|
| `AWS_ROLE_ARN` | `terraform output -raw github_actions_role_arn` |
| `S3_BUCKET` | `terraform output -raw s3_bucket` |
| `CLOUDFRONT_DISTRIBUTION_ID` | `terraform output -raw cloudfront_distribution_id` |

Uses OIDC — no long-lived AWS access keys in GitHub.

The workflow builds Lambda images with **Docker Buildx** (`linux/amd64`, `--provenance=false`, `--sbom=false`) so **CreateFunction** accepts the ECR manifest. Plain `docker build` + `docker push` from Docker Desktop often produces a manifest Lambda rejects (“image manifest … is not supported”).

## Production notes

### RDS master password

- **Save** `TF_VAR_db_password` somewhere safe the first time you run `terraform apply` (e.g. password manager). Terraform stores it in **state** as sensitive; it is **not** shown in `terraform output`.
- Every `apply` with a **new** `TF_VAR_db_password` triggers an **in-place RDS password change**. Reuse the same value for routine applies if you do not intend to rotate the master password.
- **Allowed characters** for RDS: printable ASCII **except** `/`, `@`, `"`, and space. Prefer `openssl rand -hex …` over `openssl rand -base64 …` for `TF_VAR_db_password`.

### ECR image tag and shells

- Always quote image refs: **`"${ECR_API}:latest"`**. In **zsh**, `$ECR_API:latest` can be parsed incorrectly and corrupt the repository/tag.
- Trim Terraform output newlines: `$(terraform output -raw ecr_api_url | tr -d '\n\r')`.

### PostgreSQL engine version

- If `terraform apply` fails on RDS with “Cannot find version X for postgres”, pick a version that exists in your region, for example:

  `aws rds describe-db-engine-versions --engine postgres --region ap-southeast-1 --query 'DBEngineVersions[].EngineVersion' --output text`

- The repo pins a working **16.x** in [infra/rds.tf](infra/rds.tf); adjust if your region lags.

### Database migrations

- After the first deploy, run **schema migrations** against RDS (e.g. Alembic) from a host that can reach the private instance (bastion, VPN, or one-off ECS/CodeBuild task) if your app expects tables beyond what Terraform creates.

## MCP helpers (Cursor)

This repo includes [.cursor/mcp.json](.cursor/mcp.json) with [AWS Documentation](https://github.com/awslabs/mcp/tree/main/src/aws-documentation-mcp-server) and [AWS IaC](https://github.com/awslabs/mcp/tree/main/src/aws-iac-mcp-server) servers from [awslabs/mcp](https://github.com/awslabs/mcp). Install `uv`, reload MCP in Cursor, and approve the tools when prompted. For live AWS API calls from the assistant, you can also use the managed **AWS MCP Server** ([install](https://github.com/awslabs/mcp#getting-started-with-aws)).

## Local development

For day-to-day coding without AWS:

```bash
# Backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm install && echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local && npm run dev
```

## Health check

After deploy, open `terraform output cloudfront_url` and verify the API via the same host (e.g. `/api/...` and `/health` as routed by CloudFront).
