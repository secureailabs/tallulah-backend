resource "azurerm_container_app" "container_app_backend" {
  container_app_environment_id = var.container_app_env_id
  name                         = "backend"
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  ingress {
    target_port      = 8000
    exposed_port     = 8000
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
  secret {
    name  = "storage-account-connection-string"
    value = var.storage_account_connection_string
  }
  secret {
    name  = "elastic-password"
    value = var.elastic_password
  }
  secret {
    name  = "elastic-cloud-host"
    value = var.elastic_cloud_host
  }
  secret {
    name  = "openai-api-base"
    value = var.openai_api_base
  }
  secret {
    name  = "openai-api-key"
    value = var.openai_api_key
  }
  secret {
    name  = "email-no-reply-refresh-token"
    value = var.email_no_reply_refresh_token
  }
  secret {
    name  = "google-recaptcha-secret-key"
    value = var.google_recaptcha_secret_key
  }
  secret {
    name  = "firebase-credentials"
    value = var.firebase_credentials
  }
  secret {
    name  = "dd-env"
    value = var.dd_env
  }
  secret {
    name  = "dd-api-key"
    value = var.dd_api_key
  }
  secret {
    name  = "dd-azure-subscription-id"
    value = var.dd_azure_subscription_id
  }
  secret {
    name  = "dd-azure-resource-group"
    value = var.dd_azure_resource_group
  }
  secret {
    name  = "redis-password"
    value = var.redis_password
  }
  secret {
    name  = "reddit-api-key"
    value = var.reddit_api_key
  }
  secret {
    name  = "reddit-api-secret"
    value = var.reddit_api_secret
  }
  secret {
    name  = "azure-email-from-address"
    value = var.azure_email_from_address
  }
  secret {
    name  = "azure-comm-connection-string"
    value = var.azure_comm_connection_string
  }
  secret {
    name  = "mongo-db-charts-private-key"
    value = var.mongo_db_charts_private_key
  }
  template {
    min_replicas = 1
    max_replicas = 10
    container {
      cpu    = 0.5
      image  = var.docker_image
      memory = "1Gi"
      name   = "backend"
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
        name        = "DEVOPS_KEYVAULT_URL"
        secret_name = "devops-keyvault-url"
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
      env {
        name        = "STORAGE_ACCOUNT_CONNECTION_STRING"
        secret_name = "storage-account-connection-string"
      }
      env {
        name        = "ELASTIC_PASSWORD"
        secret_name = "elastic-password"
      }
      env {
        name        = "ELASTIC_HOST"
        secret_name = "elastic-cloud-host"
      }
      env {
        name        = "OPENAI_API_BASE"
        secret_name = "openai-api-base"
      }
      env {
        name        = "OPENAI_API_KEY"
        secret_name = "openai-api-key"
      }
      env {
        name        = "EMAIL_NO_REPLY_REFRESH_TOKEN"
        secret_name = "email-no-reply-refresh-token"
      }
      env {
        name        = "GOOGLE_RECAPTCHA_SECRET_KEY"
        secret_name = "google-recaptcha-secret-key"
      }
      env {
        name        = "FIREBASE_CREDENTIALS"
        secret_name = "firebase-credentials"
      }
      env {
        name  = "FIREBASE_CREDENTIALS_FILE"
        value = ""
      }
      env {
        name        = "DD_ENV"
        secret_name = "dd-env"
      }
      env {
        name        = "DD_API_KEY"
        secret_name = "dd-api-key"
      }
      env {
        name  = "DD_LOGS_ENABLED"
        value = "true"
      }
      env {
        name  = "DD_LOGS_CONFIG_CONTAINER_COLLECT_ALL"
        value = "true"
      }
      env {
        name  = "DD_SITE"
        value = "us3.datadoghq.com"
      }
      env {
        name        = "DD_AZURE_SUBSCRIPTION_ID"
        secret_name = "dd-azure-subscription-id"
      }
      env {
        name        = "DD_AZURE_RESOURCE_GROUP"
        secret_name = "dd-azure-resource-group"
      }
      env {
        name        = "REDIS_PASSWORD"
        secret_name = "redis-password"
      }
      env {
        name        = "REDDIT_API_KEY"
        secret_name = "reddit-api-key"
      }
      env {
        name        = "REDDIT_API_SECRET"
        secret_name = "reddit-api-secret"
      }
      env {
        name        = "MONGO_DB_CHARTS_PRIVATE_KEY"
        secret_name = "mongo-db-charts-private-key"
      }
      env {
        name        = "AZURE_EMAIL_FROM_ADDRESS"
        secret_name = "azure-email-from-address"
      }
      env {
        name        = "AZURE_COMM_CONNECTION_STRING"
        secret_name = "azure-comm-connection-string"
      }
    }
  }
}
