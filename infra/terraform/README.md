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
public_base_url  = ""
certificate_arn  = ""
domain_name      = ""
hosted_zone_name = ""
oauth_allowed_redirect_uris = []
```

If you are using AWS Academy/VocLabs and see `AccessDenied` for `iam:CreateRole`, configure an existing lab instance profile instead of creating IAM resources:

```hcl
existing_instance_profile_name = "LabInstanceProfile"
```

If your lab uses a different profile name, use the name shown in the AWS Academy lab instructions.

That exposes the app through the ALB DNS over HTTP. GPT Actions require HTTPS for the final configuration. The ALB default DNS name cannot get a valid ACM certificate, so use your own domain.

If the domain is hosted in Route 53, set:

```hcl
domain_name      = "api.example.com"
hosted_zone_name = "example.com"
```

Terraform will create the ACM certificate, validate it with DNS, create an Alias record pointing to the ALB, expose HTTPS on port 443, and redirect HTTP to HTTPS. The public outputs will use `https://api.example.com`.

If you already have an ACM certificate, set it manually:

```hcl
public_base_url = "https://api.example.com"
certificate_arn = "arn:aws:acm:us-east-1:ACCOUNT_ID:certificate/..."
```

### Using Cloudflare DNS

If your DNS is managed by Cloudflare, do not set `hosted_zone_name`. Create and validate the ACM certificate manually, then point Cloudflare to the ALB:

1. In AWS Certificate Manager, request a public certificate for your domain, for example `example.com`.
2. Choose DNS validation and copy the CNAME validation record shown by ACM.
3. In Cloudflare DNS, create that validation CNAME with proxy disabled, meaning DNS only.
4. After ACM shows the certificate as issued, copy its ARN.
5. In Cloudflare DNS, create a CNAME from `@` to the ALB DNS name. Cloudflare will flatten this record at the root domain. You can start with DNS only while testing.
6. In Cloudflare SSL/TLS, use Full (strict), not Flexible.

Then set:

```hcl
public_base_url = "https://example.com"
certificate_arn = "arn:aws:acm:us-east-1:ACCOUNT_ID:certificate/..."
```

Keep these empty when using Cloudflare:

```hcl
domain_name      = ""
hosted_zone_name = ""
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

## Recovering An Existing HTTP Listener

If you enabled HTTPS after the first HTTP-only deploy and Terraform reports `DuplicateListener` on port `80`, import the existing HTTP listener before applying again:

```bash
terraform import aws_lb_listener.http arn:aws:elasticloadbalancing:us-east-1:ACCOUNT_ID:listener/app/ALB_NAME/ALB_ID/LISTENER_ID
terraform apply
```

You can find the listener ARN with:

```bash
aws elbv2 describe-listeners \
  --region us-east-1 \
  --load-balancer-arn "$(aws elbv2 describe-load-balancers \
    --region us-east-1 \
    --names mcp-aws-dev-alb \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text)" \
  --query 'Listeners[?Port==`80`].ListenerArn' \
  --output text
```

## Notes

- The ALB does not have a fixed IP. Use its DNS name, or point a domain to it using Route 53 Alias/CNAME.
- If you need fixed IPs, use AWS Global Accelerator or a different load balancer design.
- RDS is private and only accepts connections from the application security group.
- EC2 instances run in private subnets and pull the Docker image from ECR through the NAT Gateway.
- Restricted AWS Academy/VocLabs accounts may deny IAM creation. In that case, set `existing_instance_profile_name` in `terraform.tfvars` and run `terraform apply` again.
