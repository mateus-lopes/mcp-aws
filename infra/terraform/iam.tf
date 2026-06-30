resource "aws_iam_role" "app_instance" {
  count = var.existing_instance_profile_name == "" ? 1 : 0

  name = "${local.name_prefix}-app-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ecr_readonly" {
  count = var.existing_instance_profile_name == "" ? 1 : 0

  role       = aws_iam_role.app_instance[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy" "read_app_secret" {
  count = var.existing_instance_profile_name == "" ? 1 : 0

  name = "${local.name_prefix}-read-app-secret"
  role = aws_iam_role.app_instance[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.app_env.arn
      }
    ]
  })
}

resource "aws_iam_instance_profile" "app" {
  count = var.existing_instance_profile_name == "" ? 1 : 0

  name = "${local.name_prefix}-app-instance-profile"
  role = aws_iam_role.app_instance[0].name
}
