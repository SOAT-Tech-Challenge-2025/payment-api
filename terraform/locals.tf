locals {
  api_gateway_url = data.terraform_remote_state.infra.outputs.api_gateway_url
  database_dsn    = "postgresql+asyncpg://${var.database_user}:${var.database_password}@${data.aws_db_instance.db_instance.address}:${data.aws_db_instance.db_instance.port}/${var.database_name}"
}
