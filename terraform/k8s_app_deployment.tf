resource "kubernetes_deployment" "payment_api" {
  metadata {
    name      = "payment-api-deployment"
    namespace = kubernetes_namespace.payment_api.metadata[0].name
  }

  spec {
    replicas = 1
    strategy {
      type = "Recreate"
    }
    selector {
      match_labels = {
        app = "payment-api"
      }
    }

    template {
      metadata {
        labels = {
          app = "payment-api"
        }

        annotations = {
          "restarted-at" = var.force_rollout
        }
      }

      spec {
        init_container {
          name              = "payment-api-migrations"
          image             = var.docker_api_image
          image_pull_policy = "Always"
          working_dir       = "/app"
          command           = ["alembic", "upgrade", "head"]

          env_from {
            config_map_ref {
              name = kubernetes_config_map.payment_api.metadata[0].name
            }
          }

          env_from {
            secret_ref {
              name = kubernetes_secret.payment_api.metadata[0].name
            }
          }
        }

        container {
          name              = "payment-api"
          image             = var.docker_api_image
          image_pull_policy = "Always"

          port {
            container_port = 8000
          }

          resources {
            limits = {
              cpu    = "300m"
              memory = "256Mi"
            }
            requests = {
              cpu    = "100m"
              memory = "128Mi"
            }
          }

          env_from {
            config_map_ref {
              name = kubernetes_config_map.payment_api.metadata[0].name
            }
          }

          env_from {
            secret_ref {
              name = kubernetes_secret.payment_api.metadata[0].name
            }
          }
        }
      }
    }
  }
}
