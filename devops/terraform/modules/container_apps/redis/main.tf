resource "azurerm_container_app" "container_app_redis" {
  container_app_environment_id = var.container_app_env_id
  name                         = "redis"
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  ingress {
    target_port = 6379
    transport   = "tcp"
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }
  registry {
    password_secret_name = "container-registry-password"
    server               = var.container_registry_server
    username             = var.container_registry_username
  }
  secret {
    name  = "container-registry-password"
    value = var.container_registry_password
  }
  secret {
    name  = "redis-password"
    value = var.redis_password
  }
  template {
    min_replicas = 1
    max_replicas = 10
    container {
      cpu    = 0.5
      image  = var.docker_image
      memory = "1Gi"
      name   = "redis"
      env {
        name        = "REDIS_PASSWORD"
        secret_name = "redis-password"
      }
    }
  }
}
