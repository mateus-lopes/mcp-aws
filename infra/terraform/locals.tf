locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  effective_public_base_url = var.public_base_url != "" ? trimsuffix(var.public_base_url, "/") : "http://${aws_lb.app.dns_name}"
  image_uri                 = "${aws_ecr_repository.app.repository_url}:${var.container_image_tag}"
}
