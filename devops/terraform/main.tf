data "azurerm_key_vault" "keyvault_devops" {
  name                = var.devops_keyvault_name
  resource_group_name = var.devops_resource_group_name
}

data "azurerm_key_vault_secrets" "keyvault_secrets" {
  key_vault_id = data.azurerm_key_vault.keyvault_devops.id
}

data "azurerm_key_vault_secret" "keyvault_secrets" {
  for_each     = toset(data.azurerm_key_vault_secrets.keyvault_secrets.names)
  name         = each.key
  key_vault_id = data.azurerm_key_vault.keyvault_devops.id
}

data "azurerm_key_vault_certificates" "keyvault_certs" {
  key_vault_id = data.azurerm_key_vault.keyvault_devops.id
}

data "azurerm_key_vault_certificate" "keyvault_certs" {
  for_each     = toset(data.azurerm_key_vault_certificates.keyvault_certs.names)
  name         = each.key
  key_vault_id = data.azurerm_key_vault.keyvault_devops.id
}

module "tls_certificates" {
  source                   = "./modules/tls_certificate"
  godaddy_api_key          = data.azurerm_key_vault_secret.keyvault_secrets["godaddy-key"].value
  godaddy_api_secret       = data.azurerm_key_vault_secret.keyvault_secrets["godaddy-secret"].value
  ssl_certificate_password = data.azurerm_key_vault_secret.keyvault_secrets["ssl-certificate-password"].value
  host_name                = var.host_name
}

module "tls_certificates_2" {
  source                   = "./modules/tls_certificate"
  godaddy_api_key          = data.azurerm_key_vault_secret.keyvault_secrets["godaddy-key"].value
  godaddy_api_secret       = data.azurerm_key_vault_secret.keyvault_secrets["godaddy-secret"].value
  ssl_certificate_password = data.azurerm_key_vault_secret.keyvault_secrets["ssl-certificate-password"].value
  host_name                = var.host_name_2
}

module "resource_group" {
  source                  = "./modules/resource_group"
  resource_group_name     = var.resource_group_name
  resource_group_location = "westus"
}

module "virtual_network" {
  source               = "./modules/virtual_network"
  virtual_network_name = "vnet"
  resource_group_name  = module.resource_group.resource_group_name
}

module "container_apps_env" {
  source                   = "./modules/container_apps_env"
  name                     = "container-apps-env"
  resource_group_name      = module.resource_group.resource_group_name
  infrastructure_subnet_id = module.virtual_network.container_apps_subnet_id
}

module "keyvault" {
  source              = "./modules/keyvault"
  keyvault_name       = "keyvault"
  resource_group_name = module.resource_group.resource_group_name
  azure_tenant_id     = data.azurerm_key_vault_secret.keyvault_secrets["azure-tenant-id"].value
  azure_object_id     = data.azurerm_key_vault_secret.keyvault_secrets["azure-object-id"].value
  subnet_id           = module.virtual_network.container_apps_subnet_id
}


module "public_ip" {
  source              = "./modules/public_ip"
  name                = "gateway-frontend-ip"
  resource_group_name = module.resource_group.resource_group_name
}

module "application_gateway" {
  source                   = "./modules/application_gateway"
  resource_group_name      = module.resource_group.resource_group_name
  container_app_subnet_id  = module.virtual_network.container_apps_subnet_id
  gateway_subnet_id        = module.virtual_network.gateway_subnet_id
  backend_address          = "backend.${module.container_apps_env.container_app_environment_default_domain}"
  ui_address               = "frontend.${module.container_apps_env.container_app_environment_default_domain}"
  gateway_public_ip_id     = module.public_ip.public_ip_id
  react_app_address        = "ui.${module.container_apps_env.container_app_environment_default_domain}"
  ssl_certificate_password = data.azurerm_key_vault_secret.keyvault_secrets["ssl-certificate-password"].value
  ssl_certificate_pfx      = module.tls_certificates.certificate_pfx
  ssl_certificate_pfx_2    = module.tls_certificates_2.certificate_pfx
  host_name                = var.host_name
  host_name_2              = var.host_name_2
}

module "private_dns_zone" {
  source                               = "./modules/private_dns_zone"
  resource_group_name                  = module.resource_group.resource_group_name
  private_dns_zone_name                = module.container_apps_env.container_app_environment_default_domain
  virtual_network_id                   = module.virtual_network.virtual_network_id
  container_apps_environment_static_ip = module.container_apps_env.container_app_environment_static_ip
}

module "container_app_backend" {
  source                            = "./modules/container_apps/backend"
  resource_group_name               = module.resource_group.resource_group_name
  container_app_env_id              = module.container_apps_env.container_app_environment_id
  docker_image                      = format("%s/%s", var.container_registry_server, var.backend_container_image_tag)
  container_registry_server         = var.container_registry_server
  container_registry_username       = data.azurerm_key_vault_secret.keyvault_secrets["container-registry-username"].value
  container_registry_password       = data.azurerm_key_vault_secret.keyvault_secrets["container-registry-password"].value
  azure_client_id                   = data.azurerm_key_vault_secret.keyvault_secrets["azure-client-id"].value
  azure_client_secret               = data.azurerm_key_vault_secret.keyvault_secrets["azure-client-secret"].value
  azure_tenant_id                   = data.azurerm_key_vault_secret.keyvault_secrets["azure-tenant-id"].value
  keyvault_url                      = module.keyvault.keyvault_url
  devops_keyvault_url               = data.azurerm_key_vault.keyvault_devops.vault_uri
  jwt_secret                        = data.azurerm_key_vault_secret.keyvault_secrets["jwt-secret"].value
  mongo_connection_url              = data.azurerm_key_vault_secret.keyvault_secrets["mongo-connection-url"].value
  outlook_client_id                 = data.azurerm_key_vault_secret.keyvault_secrets["outlook-client-id"].value
  outlook_client_secret             = data.azurerm_key_vault_secret.keyvault_secrets["outlook-client-secret"].value
  outlook_tenant_id                 = data.azurerm_key_vault_secret.keyvault_secrets["outlook-tenant-id"].value
  outlook_redirect_uri              = data.azurerm_key_vault_secret.keyvault_secrets["outlook-redirect-uri"].value
  password_pepper                   = data.azurerm_key_vault_secret.keyvault_secrets["password-pepper"].value
  rabbit_mq_host                    = data.azurerm_key_vault_secret.keyvault_secrets["rabbit-mq-host"].value
  refresh_secret                    = data.azurerm_key_vault_secret.keyvault_secrets["refresh-secret"].value
  storage_container_sas_url         = "TODO"
  tallulah_admin_password           = data.azurerm_key_vault_secret.keyvault_secrets["tallulah-admin-password"].value
  storage_account_connection_string = module.storage_account.storage_account_connection_string
  elastic_password                  = data.azurerm_key_vault_secret.keyvault_secrets["elastic-password"].value
  elastic_cloud_host                = data.azurerm_key_vault_secret.keyvault_secrets["elastic-cloud-host"].value
  openai_api_base                   = data.azurerm_key_vault_secret.keyvault_secrets["openai-api-base"].value
  openai_api_key                    = data.azurerm_key_vault_secret.keyvault_secrets["openai-api-key"].value
  email_no_reply_refresh_token      = data.azurerm_key_vault_secret.keyvault_secrets["email-no-reply-refresh-token"].value
  google_recaptcha_secret_key       = data.azurerm_key_vault_secret.keyvault_secrets["google-recaptcha-secret-key"].value
  firebase_credentials              = data.azurerm_key_vault_secret.keyvault_secrets["firebase-credentials"].value
}

module "container_app_rabbit_mq" {
  source                      = "./modules/container_apps/rabbit_mq"
  resource_group_name         = module.resource_group.resource_group_name
  container_app_env_id        = module.container_apps_env.container_app_environment_id
  docker_image                = format("%s/%s", var.container_registry_server, var.rabbitmq_container_image_tag)
  container_registry_server   = var.container_registry_server
  container_registry_username = data.azurerm_key_vault_secret.keyvault_secrets["container-registry-username"].value
  container_registry_password = data.azurerm_key_vault_secret.keyvault_secrets["container-registry-password"].value
  rabbit_mq_password          = data.azurerm_key_vault_secret.keyvault_secrets["rabbit-mq-password"].value
  rabbit_mq_user              = data.azurerm_key_vault_secret.keyvault_secrets["rabbit-mq-user"].value
}

module "container_app_classifier" {
  source                      = "./modules/container_apps/classifier"
  resource_group_name         = module.resource_group.resource_group_name
  container_app_env_id        = module.container_apps_env.container_app_environment_id
  docker_image                = format("%s/%s", var.container_registry_server, var.classifier_container_image_tag)
  container_registry_server   = var.container_registry_server
  container_registry_username = data.azurerm_key_vault_secret.keyvault_secrets["container-registry-username"].value
  container_registry_password = data.azurerm_key_vault_secret.keyvault_secrets["container-registry-password"].value
  azure_client_id             = data.azurerm_key_vault_secret.keyvault_secrets["azure-client-id"].value
  azure_client_secret         = data.azurerm_key_vault_secret.keyvault_secrets["azure-client-secret"].value
  azure_tenant_id             = data.azurerm_key_vault_secret.keyvault_secrets["azure-tenant-id"].value
  devops_keyvault_url         = data.azurerm_key_vault.keyvault_devops.vault_uri
  mongo_connection_url        = data.azurerm_key_vault_secret.keyvault_secrets["mongo-connection-url"].value
  rabbit_mq_host              = data.azurerm_key_vault_secret.keyvault_secrets["rabbit-mq-host"].value
}


module "container_app_frontend" {
  source                      = "./modules/container_apps/frontend"
  resource_group_name         = module.resource_group.resource_group_name
  container_app_env_id        = module.container_apps_env.container_app_environment_id
  docker_image                = format("%s/%s", var.container_registry_server, var.ui_container_image_tag)
  container_registry_server   = var.container_registry_server
  container_registry_username = data.azurerm_key_vault_secret.keyvault_secrets["container-registry-username"].value
  container_registry_password = data.azurerm_key_vault_secret.keyvault_secrets["container-registry-password"].value
}


module "container_app_logstash" {
  source                      = "./modules/container_apps/logstash"
  resource_group_name         = module.resource_group.resource_group_name
  container_app_env_id        = module.container_apps_env.container_app_environment_id
  docker_image                = format("%s/%s", var.container_registry_server, var.logstash_container_image_tag)
  container_registry_server   = var.container_registry_server
  container_registry_username = data.azurerm_key_vault_secret.keyvault_secrets["container-registry-username"].value
  container_registry_password = data.azurerm_key_vault_secret.keyvault_secrets["container-registry-password"].value
  elastic_cloud_username      = data.azurerm_key_vault_secret.keyvault_secrets["elastic-username"].value
  elastic_cloud_password      = data.azurerm_key_vault_secret.keyvault_secrets["elastic-password"].value
  elastic_cloud_host          = data.azurerm_key_vault_secret.keyvault_secrets["elastic-cloud-host"].value
}


module "storage_account" {
  source              = "./modules/storage_account"
  name                = "tallulahstorage"
  resource_group_name = module.resource_group.resource_group_name
}
