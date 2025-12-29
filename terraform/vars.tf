variable "region" {
  description = "The AWS region to deploy resources in"
  default     = "us-east-1"
}

variable "force_rollout" {
  description = "A dummy variable to force redeployment of resources"
  type        = string
  default     = ""
}

variable "docker_api_image" {
  description = "The Docker image for the Payment API"
  default     = "public.ecr.aws/p6c0d2v5/fiap-soat-techchallenge-payment:latest"
}

variable "app_title" {
  description = "The title of the Payment API"
  default     = "SOAT Tech Challenge Payment API"
}

variable "app_version" {
  description = "The version of the Payment API"
  default     = "1.0.0"
}

variable "app_environment" {
  description = "The environment for the Payment API"
  default     = "production"
}

variable "app_root_path" {
  description = "The root path for the Payment API"
  default     = "/soat-fast-food"
}

variable "aws_account_id" {
  description = "The AWS account ID to interact with AWS services"
  sensitive   = true
}

variable "aws_access_key_id" {
  description = "The AWS access key ID to interact with AWS services"
  sensitive   = true
}

variable "aws_secret_access_key" {
  description = "The AWS secret access key to interact with AWS services"
  sensitive   = true
}

variable "database_name" {
  description = "The database name in the Postgres instance"
  sensitive   = true
}

variable "database_user" {
  description = "The username for the Postgres instance"
  sensitive   = true
}

variable "database_password" {
  description = "The password for the Postgres instance"
  sensitive   = true
}

variable "database_echo" {
  description = "Determine if SQLAlchemy should log SQL queries"
  type        = bool
  default     = false
}

variable "http_client_timeout" {
  description = "The timeout for the HTTP client in seconds"
  type        = number
  default     = 10
}

variable "mercado_pago_access_token" {
  description = "The access token for Mercado Pago"
  sensitive   = true
}

variable "mercado_pago_user_id" {
  description = "The integration user ID for Mercado Pago"
  sensitive   = true
}

variable "mercado_pago_pos" {
  description = "The point of sale identifier for Mercado Pago"
  sensitive   = true
}

variable "mercado_pago_webhook_key" {
  description = "The internal token for validating Mercado Pago webhooks"
  sensitive   = true
}

variable "order_created_listener_queue_name" {
  description = "The name of the SQS queue to listen for order created events"
}

variable "payment_closed_publisher_group_id" {
  description = "The ID of the publisher group for payment closed events"
}
