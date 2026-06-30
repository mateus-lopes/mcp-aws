#!/bin/bash
set -euxo pipefail

dnf update -y
dnf install -y docker awscli jq

systemctl enable --now docker

aws ecr get-login-password --region "${aws_region}" | docker login --username AWS --password-stdin "$(echo "${image_uri}" | cut -d/ -f1)"

aws secretsmanager get-secret-value \
  --secret-id "${secret_arn}" \
  --region "${aws_region}" \
  --query SecretString \
  --output text > /opt/mcp-aws-secret.json

jq -r 'to_entries[] | "\(.key)=\(.value|tostring)"' /opt/mcp-aws-secret.json > /opt/mcp-aws.env
chmod 600 /opt/mcp-aws.env

docker pull "${image_uri}"
docker stop mcp-aws || true
docker rm mcp-aws || true
docker run -d \
  --name mcp-aws \
  --restart unless-stopped \
  --env-file /opt/mcp-aws.env \
  -p "${app_port}:8000" \
  "${image_uri}"
