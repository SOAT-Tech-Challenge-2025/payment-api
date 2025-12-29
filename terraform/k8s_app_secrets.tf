resource "kubernetes_secret" "payment_api" {
  metadata {
    name      = "payment-api-secret"
    namespace = kubernetes_namespace.payment_api.metadata[0].name
  }

  type = "Opaque"

  data = {
    DATABASE_DSN                       = local.database_dsn
    AWS_ACCOUNT_ID                     = var.aws_account_id
    AWS_ACCESS_KEY_ID                  = var.aws_access_key_id
    AWS_SECRET_ACCESS_KEY              = var.aws_secret_access_key
    MERCADO_PAGO_ACCESS_TOKEN          = var.mercado_pago_access_token
    MERCADO_PAGO_POS                   = var.mercado_pago_pos
    MERCADO_PAGO_USER_ID               = var.mercado_pago_user_id
    MERCADO_PAGO_WEBHOOK_KEY           = var.mercado_pago_webhook_key
    PAYMENT_CLOSED_PUBLISHER_TOPIC_ARN = data.terraform_remote_state.database.outputs.payment_closed_topic_arn
    PAYMENT_CLOSED_PUBLISHER_GROUP_ID  = var.payment_closed_publisher_group_id
  }
}
