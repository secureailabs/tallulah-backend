resource "azurerm_container_app" "container_app_frontend" {
  container_app_environment_id = var.container_app_env_id
  name                         = "frontend"
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  ingress {
    target_port      = 3000
    exposed_port     = 500
    transport        = "tcp"
    external_enabled = true
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
  template {
    min_replicas = 1
    max_replicas = 10
    container {
      cpu    = 0.5
      image  = var.docker_image
      memory = "1Gi"
      name   = "frontend"
    }
  }
}
