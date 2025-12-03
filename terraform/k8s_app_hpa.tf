resource "kubernetes_horizontal_pod_autoscaler_v2" "payment_api" {
  metadata {
    name      = "payment-api-hpa"
    namespace = kubernetes_namespace.payment_api.metadata[0].name
  }

  spec {
    scale_target_ref {
      api_version = "apps/v1"
      kind        = "Deployment"
      name        = kubernetes_deployment.payment_api.metadata[0].name
    }

    min_replicas = 1
    max_replicas = 3

    metric {
      type = "Resource"

      resource {
        name = "cpu"

        target {
          type                = "Utilization"
          average_utilization = 90
        }
      }
    }

    metric {
      type = "Resource"

      resource {
        name = "memory"

        target {
          type                = "Utilization"
          average_utilization = 90
        }
      }
    }
  }
}
