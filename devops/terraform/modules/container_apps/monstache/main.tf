resource "azurerm_container_app" "container_app_monstache" {
  container_app_environment_id = var.container_app_env_id
  name                         = "monstache"
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
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
    name  = "mongo-url"
    value = var.mongo_url
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
  secret {
    name  = "mongo-certificate"
    value = var.mongo_certificate
  }
  template {
    min_replicas = 1
    max_replicas = 10
    volume {
      name         = "certificates"
      storage_type = "Secret"
    }
    container {
      cpu    = 0.5
      image  = var.docker_image
      memory = "1Gi"
      name   = "monstache"
      volume_mounts {
        name = "certificates"
        path = "/mnt/certificates"
      }
      env {
        name        = "MONGO_URL"
        secret_name = "mongo-url"
      }
      env {
        name        = "MONSTACHE_ES_URLS"
        secret_name = "elastic-cloud-host"
      }
      env {
        name        = "MONSTACHE_ES_USER"
        secret_name = "elastic-cloud-username"
      }
      env {
        name        = "MONSTACHE_ES_PASS"
        secret_name = "elastic-cloud-password"
      }
      env {
        name  = "MONSTACHE_CHANGE_STREAM_NS"
        value = var.monstache_change_stream_ns
      }
    }
  }
}
