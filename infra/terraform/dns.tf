data "aws_route53_zone" "app" {
  count = local.custom_domain_enabled ? 1 : 0

  name         = "${trimsuffix(var.hosted_zone_name, ".")}."
  private_zone = false
}

resource "aws_acm_certificate" "app" {
  count = local.managed_certificate_enabled ? 1 : 0

  domain_name       = var.domain_name
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-cert"
  })
}

resource "aws_route53_record" "app_cert_validation" {
  for_each = local.managed_certificate_enabled ? {
    for option in aws_acm_certificate.app[0].domain_validation_options : option.domain_name => {
      name   = option.resource_record_name
      record = option.resource_record_value
      type   = option.resource_record_type
    }
  } : {}

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.app[0].zone_id
}

resource "aws_acm_certificate_validation" "app" {
  count = local.managed_certificate_enabled ? 1 : 0

  certificate_arn         = aws_acm_certificate.app[0].arn
  validation_record_fqdns = [for record in aws_route53_record.app_cert_validation : record.fqdn]
}

resource "aws_route53_record" "app_alias" {
  count = local.custom_domain_enabled ? 1 : 0

  name    = var.domain_name
  type    = "A"
  zone_id = data.aws_route53_zone.app[0].zone_id

  alias {
    evaluate_target_health = true
    name                   = aws_lb.app.dns_name
    zone_id                = aws_lb.app.zone_id
  }
}
