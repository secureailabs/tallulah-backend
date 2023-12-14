resource "azurerm_container_app" "container_app_logstash" {
  container_app_environment_id = var.container_app_env_id
  name                         = "logstash"
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  ingress {
    target_port = 5044
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
    name  = "elastic-cloud-username"
    value = var.elastic_cloud_username
  }
  secret {
    name  = "elastic-cloud-password"
    value = var.elastic_cloud_password
  }
  secret {
    name  = "elastic-cloud-host"
    value = var.elastic_cloud_host
  }
  template {
    min_replicas = 1
    max_replicas = 10
    container {
      cpu    = 0.5
      image  = var.docker_image
      memory = "1Gi"
      name   = "logstash"
      env {
        name        = "ELASTIC_CLOUD_USERNAME"
        secret_name = "elastic-cloud-username"
      }
      env {
        name        = "ELASTIC_CLOUD_PASSWORD"
        secret_name = "elastic-cloud-password"
      }
      env {
        name        = "ELASTIC_CLOUD_HOST"
        secret_name = "elastic-cloud-host"
      }
    }
  }
}
