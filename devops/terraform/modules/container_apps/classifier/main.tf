resource "azurerm_container_app" "container_app_classifier" {
  container_app_environment_id = var.container_app_env_id
  name                         = "classifier"
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
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
    name  = "devops-keyvault-url"
    value = var.devops_keyvault_url
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
    name  = "mongo-connection-url"
    value = var.mongo_connection_url
  }
  secret {
    name  = "rabbit-mq-host"
    value = var.rabbit_mq_host
  }
  template {
    min_replicas = 1
    max_replicas = 10
    container {
      cpu    = 0.5
      image  = var.docker_image
      memory = "1Gi"
      name   = "classifier"
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
        name        = "DEVOPS_KEYVAULT_URL"
        secret_name = "devops-keyvault-url"
      }
      env {
        name  = "RABBIT_MQ_PORT"
        value = "5672"
      }
      env {
        name  = "RABBIT_MQ_QUEUE_NAME"
        value = "email_queue"
      }
      env {
        name        = "RABBIT_MQ_HOSTNAME"
        secret_name = "rabbit-mq-host"
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
        name  = "MONGODB_COLLECTION_NAME"
        value = "emails"
      }
    }
  }
}
