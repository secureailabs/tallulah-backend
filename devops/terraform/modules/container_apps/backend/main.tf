resource "azurerm_container_app" "container_app_backend" {
  container_app_environment_id = var.container_app_env_id
  name                         = "tallulah-backend"
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  ingress {
    external_enabled = true
    target_port      = 8000
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
    name  = "azure-client-id"
    value = var.azure_client_id
  }
  secret {
    name  = "azure-client-secret"
    value = var.azure_client_secret
  }
  secret {
    name  = "azure-keyvault-url"
    value = var.keyvault_url
  }
  secret {
    name  = "azure-tenant-id"
    value = var.azure_tenant_id
  }
  secret {
    name  = "container-registry-password"
    value = var.container_registry_password
  }
  secret {
    name  = "jwt-secret"
    value = var.jwt_secret
  }
  secret {
    name  = "mongo-connection-url"
    value = var.mongo_connection_url
  }
  secret {
    name  = "outlook-client-id"
    value = var.outlook_client_id
  }
  secret {
    name  = "outlook-client-secret"
    value = var.outlook_client_secret
  }
  secret {
    name  = "password-pepper"
    value = var.password_pepper
  }
  secret {
    name  = "rabbit-mq-host"
    value = var.rabbit_mq_host
  }
  secret {
    name  = "refresh-secret"
    value = var.refresh_secret
  }
  secret {
    name  = "storage-container-sas-url"
    value = var.storage_container_sas_url
  }
  secret {
    name  = "tallulah-admin-password"
    value = var.tallulah_admin_password
  }
  template {
    min_replicas = 1
    max_replicas = 10
    container {
      cpu    = 0.5
      image  = var.docker_image
      memory = "1Gi"
      name   = "tallulah-backend"
      env {
        name = "SLACK_WEBHOOK"
      }
      env {
        name  = "OUTLOOK_REDIRECT_URI"
        value = var.outlook_redirect_uri
      }
      env {
        name  = "OUTLOOK_TENANT_ID"
        value = var.outlook_tenant_id
      }
      env {
        name  = "MONGO_DB_NAME"
        value = var.resource_group_name
      }
      env {
        name        = "MONGO_CONNECTION_URL"
        secret_name = "mongo-connection-url"
      }
      env {
        name        = "JWT_SECRET"
        secret_name = "jwt-secret"
      }
      env {
        name        = "REFRESH_SECRET"
        secret_name = "refresh-secret"
      }
      env {
        name        = "PASSWORD_PEPPER"
        secret_name = "password-pepper"
      }
      env {
        name        = "OUTLOOK_CLIENT_ID"
        secret_name = "outlook-client-id"
      }
      env {
        name        = "OUTLOOK_CLIENT_SECRET"
        secret_name = "outlook-client-secret"
      }
      env {
        name        = "AZURE_CLIENT_ID"
        secret_name = "azure-client-id"
      }
      env {
        name        = "AZURE_CLIENT_SECRET"
        secret_name = "azure-client-secret"
      }
      env {
        name        = "AZURE_TENANT_ID"
        secret_name = "azure-tenant-id"
      }
      env {
        name        = "AZURE_KEYVAULT_URL"
        secret_name = "azure-keyvault-url"
      }
      env {
        name        = "STORAGE_CONTAINER_SAS_URL"
        secret_name = "storage-container-sas-url"
      }
      env {
        name  = "RABBIT_MQ_QUEUE_NAME"
        value = "email_queue"
      }
      env {
        name        = "RABBIT_MQ_HOST"
        secret_name = "rabbit-mq-host"
      }
      env {
        name        = "TALLULAH_ADMIN_PASSWORD"
        secret_name = "tallulah-admin-password"
      }
    }
  }
}
