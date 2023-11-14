resource "azurerm_container_app" "container_app_frontend" {
  container_app_environment_id = var.container_app_env_id
  name                         = "tallulah-frontend"
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  ingress {
    external_enabled = true
    target_port      = 80
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
    container {
      cpu    = 0.5
      image  = var.docker_image
      memory = "1Gi"
      name   = "tallulah-frontend"
    }
  }
}
