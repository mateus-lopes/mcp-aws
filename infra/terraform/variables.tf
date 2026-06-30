variable "aws_region" {
  type        = string
  description = "AWS region where the infrastructure will be created."
  default     = "us-east-1"
}

variable "project_name" {
  type        = string
  description = "Project name used in resource names."
  default     = "mcp-aws"
}

variable "environment" {
  type        = string
  description = "Environment name used in resource names and tags."
  default     = "dev"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC."
  default     = "10.40.0.0/16"
}

variable "az_count" {
  type        = number
  description = "Number of availability zones to use."
  default     = 2
}

variable "app_port" {
  type        = number
  description = "Port exposed by the FastAPI container."
  default     = 8000
}

variable "instance_type" {
  type        = string
  description = "EC2 instance type for the application Auto Scaling Group."
  default     = "t3.micro"
}

variable "desired_capacity" {
  type        = number
  description = "Desired number of EC2 instances."
  default     = 1
}

variable "min_size" {
  type        = number
  description = "Minimum number of EC2 instances."
  default     = 1
}

variable "max_size" {
  type        = number
  description = "Maximum number of EC2 instances."
  default     = 2
}

variable "db_name" {
  type        = string
  description = "PostgreSQL database name."
  default     = "mcpaws"
}

variable "db_username" {
  type        = string
  description = "PostgreSQL master username."
  default     = "mcpaws_user"
}

variable "db_instance_class" {
  type        = string
  description = "RDS instance class."
  default     = "db.t4g.micro"
}

variable "db_allocated_storage" {
  type        = number
  description = "RDS allocated storage in GB."
  default     = 20
}

variable "db_multi_az" {
  type        = bool
  description = "Whether to enable Multi-AZ for RDS."
  default     = false
}

variable "container_image_tag" {
  type        = string
  description = "Docker image tag pulled from ECR by EC2 instances."
  default     = "latest"
}

variable "public_base_url" {
  type        = string
  description = "Public URL used by OpenAPI servers and OAuth callbacks. Leave empty to use the ALB DNS over HTTP."
  default     = ""
}

variable "oauth_allowed_redirect_uris" {
  type        = list(string)
  description = "Allowed ChatGPT OAuth redirect URIs."
  default     = []
}

variable "certificate_arn" {
  type        = string
  description = "Optional ACM certificate ARN. When set, the ALB exposes HTTPS on 443 and redirects HTTP to HTTPS."
  default     = ""
}

variable "existing_instance_profile_name" {
  type        = string
  description = "Optional existing EC2 instance profile name. Use this in restricted AWS accounts such as AWS Academy/VocLabs where iam:CreateRole is denied."
  default     = ""
}
