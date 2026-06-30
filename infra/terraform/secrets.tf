resource "random_password" "secret_key" {
  length  = 48
  special = false
}

resource "random_password" "oauth_client_secret" {
  length  = 48
  special = false
}

resource "aws_secretsmanager_secret" "app_env" {
  name                    = "${local.name_prefix}/app-env"
  recovery_window_in_days = 0

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "app_env" {
  secret_id = aws_secretsmanager_secret.app_env.id

  secret_string = jsonencode({
    DATABASE_URL                = "postgresql+psycopg://${var.db_username}:${random_password.db_password.result}@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${var.db_name}"
    SECRET_KEY                  = random_password.secret_key.result
    ALGORITHM                   = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = "60"
    OAUTH_CLIENT_ID             = "${local.name_prefix}-gpt"
    OAUTH_CLIENT_SECRET         = random_password.oauth_client_secret.result
    OAUTH_ALLOWED_REDIRECT_URIS = join(",", var.oauth_allowed_redirect_uris)
    OAUTH_AUTH_CODE_EXPIRE_MINUTES   = "10"
    OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES = "60"
    PUBLIC_BASE_URL             = local.effective_public_base_url
  })
}
