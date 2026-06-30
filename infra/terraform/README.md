# MCP AWS Terraform Deploy

This Terraform stack creates a first production-style AWS deployment:

- VPC with public, private app, and private database subnets
- Internet Gateway and NAT Gateway
- Application Load Balancer
- Auto Scaling Group with EC2 instances running Docker
- ECR repository for the backend image
- Private RDS PostgreSQL
- Secrets Manager secret with application environment variables
- Security groups restricted by layer

## Important Cost Notes

This creates billable resources, especially NAT Gateway, ALB, EC2, and RDS.
Destroy the stack when you are done testing:

```bash
terraform destroy
```

## Prerequisites

- AWS CLI configured locally
- Terraform installed
- Docker installed
- Permission to create VPC, EC2, ALB, Auto Scaling, ECR, RDS, IAM, and Secrets Manager resources

## 1. Configure Variables

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` if needed.

For the first deploy, you can leave:

```hcl
public_base_url = ""
certificate_arn = ""
oauth_allowed_redirect_uris = []
```

If you are using AWS Academy/VocLabs and see `AccessDenied` for `iam:CreateRole`, configure an existing lab instance profile instead of creating IAM resources:

```hcl
existing_instance_profile_name = "LabInstanceProfile"
```

If your lab uses a different profile name, use the name shown in the AWS Academy lab instructions.

That exposes the app through the ALB DNS over HTTP. GPT Actions require HTTPS for the final configuration, so later use a domain plus ACM certificate and set:

```hcl
public_base_url = "https://your-domain.com"
certificate_arn = "arn:aws:acm:us-east-1:ACCOUNT_ID:certificate/..."
```

## 2. Create ECR First

Create only the ECR repository first, so there is a place to push the Docker image:

```bash
terraform init
terraform apply -target=aws_ecr_repository.app -target=aws_ecr_lifecycle_policy.app
```

Get the repository URL:

```bash
ECR_REPO="$(terraform output -raw ecr_repository_url)"
AWS_REGION="$(terraform output -raw ecr_repository_url | cut -d. -f4)"
```

If the region extraction is not correct for your shell, set it manually:

```bash
AWS_REGION="us-east-1"
```

## 3. Build And Push The Backend Image

Run this from the repository root:

```bash
cd ../..
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$(echo "$ECR_REPO" | cut -d/ -f1)"

docker buildx build --platform linux/amd64 -f backend/Dockerfile -t "$ECR_REPO:latest" --push .
```

## 4. Apply The Full Infrastructure

```bash
cd infra/terraform
terraform apply
```

Terraform will output:

- `app_url`
- `openapi_gpt_url`
- `privacy_url`
- `oauth_authorize_url`
- `oauth_token_url`
- `oauth_client_id`

## 5. Test The App

```bash
curl "$(terraform output -raw app_url)/health"
```

Expected:

```json
{"status":"ok"}
```

## 6. Configure GPT Action

Use the Terraform outputs:

```text
Schema URL: openapi_gpt_url
Privacy policy: privacy_url
Authorization URL: oauth_authorize_url
Token URL: oauth_token_url
Client ID: oauth_client_id
```

Get the OAuth client secret from Secrets Manager:

```bash
aws secretsmanager get-secret-value \
  --region "$AWS_REGION" \
  --secret-id "$(terraform output -raw app_secret_arn)" \
  --query SecretString \
  --output text
```

Use the `OAUTH_CLIENT_SECRET` value in the GPT Action authentication settings.

After ChatGPT shows the OAuth callback URL, add it to `oauth_allowed_redirect_uris` in `terraform.tfvars` and run:

```bash
terraform apply
```

## Notes

- The ALB does not have a fixed IP. Use its DNS name, or point a domain to it using Route 53 Alias/CNAME.
- If you need fixed IPs, use AWS Global Accelerator or a different load balancer design.
- RDS is private and only accepts connections from the application security group.
- EC2 instances run in private subnets and pull the Docker image from ECR through the NAT Gateway.
- Restricted AWS Academy/VocLabs accounts may deny IAM creation. In that case, set `existing_instance_profile_name` in `terraform.tfvars` and run `terraform apply` again.
