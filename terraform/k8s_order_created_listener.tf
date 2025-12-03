resource "kubernetes_deployment" "order_created_listener" {
  metadata {
    name      = "order-created-listener-deployment"
    namespace = kubernetes_namespace.payment_api.metadata[0].name
  }

  spec {
    replicas = 1
    strategy {
      type = "Recreate"
    }
    selector {
      match_labels = {
        app = "order-created-listener"
      }
    }

    template {
      metadata {
        labels = {
          app = "order-created-listener"
        }

        annotations = {
          "restarted-at" = var.force_rollout
        }
      }

      spec {
        container {
          name              = "order-created-listener"
          image             = var.docker_api_image
          image_pull_policy = "Always"
          command           = ["sh", "/app/docker-entrypoint/start_order_created_listener.sh"]

          resources {
            limits = {
              cpu    = "500m"
              memory = "1Gi"
            }
            requests = {
              cpu    = "250m"
              memory = "512Mi"
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
