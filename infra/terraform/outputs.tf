output "alb_dns_name" {
  description = "Public ALB DNS name."
  value       = aws_lb.app.dns_name
}

output "app_url" {
  description = "Public application URL."
  value       = local.effective_public_base_url
}

output "openapi_gpt_url" {
  description = "Schema URL to import in GPT Actions."
  value       = "${local.effective_public_base_url}/openapi-gpt.json"
}

output "privacy_url" {
  description = "Privacy policy URL for GPT Actions."
  value       = "${local.effective_public_base_url}/privacy"
}

output "oauth_authorize_url" {
  description = "OAuth authorization URL for GPT Actions."
  value       = "${local.effective_public_base_url}/oauth/authorize"
}

output "oauth_token_url" {
  description = "OAuth token URL for GPT Actions."
  value       = "${local.effective_public_base_url}/oauth/token"
}

output "ecr_repository_url" {
  description = "ECR repository URL for the backend image."
  value       = aws_ecr_repository.app.repository_url
}

output "oauth_client_id" {
  description = "OAuth client ID configured for the GPT Action."
  value       = "${local.name_prefix}-gpt"
}

output "app_secret_arn" {
  description = "Secrets Manager ARN containing app environment variables."
  value       = aws_secretsmanager_secret.app_env.arn
}
