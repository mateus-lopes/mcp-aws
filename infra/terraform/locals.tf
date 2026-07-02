locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  managed_certificate_enabled = var.certificate_arn == "" && var.domain_name != "" && var.hosted_zone_name != ""
  custom_domain_enabled       = var.domain_name != "" && var.hosted_zone_name != ""
  https_listener_enabled      = var.certificate_arn != "" || local.managed_certificate_enabled
  selected_certificate_arn    = var.certificate_arn != "" ? var.certificate_arn : (local.managed_certificate_enabled ? aws_acm_certificate_validation.app[0].certificate_arn : "")
  effective_public_base_url   = var.public_base_url != "" ? trimsuffix(var.public_base_url, "/") : (local.https_listener_enabled && var.domain_name != "" ? "https://${var.domain_name}" : "http://${aws_lb.app.dns_name}")
  image_uri                   = "${aws_ecr_repository.app.repository_url}:${var.container_image_tag}"
}
