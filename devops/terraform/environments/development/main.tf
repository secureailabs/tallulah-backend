module "resource_group" {
  source                     = "../../modules/resource_group"
  resource_group_name        = var.resource_group_name
  resource_group_location    = "westus"
}

module "virtual_network" {
  source               = "../../modules/virtual_network"
  virtual_network_name = "vnet"
  resource_group_name  = module.resource_group.resource_group_name
}

module "container_apps_env" {
  source                   = "../../modules/container_apps_env"
  name                     = "container-apps-env"
  resource_group_name      = module.resource_group.resource_group_name
  infrastructure_subnet_id = module.virtual_network.container_apps_subnet_id
}

module "keyvault" {
  source              = "../../modules/keyvault"
  keyvault_name       = "keyvault"
  resource_group_name = module.resource_group.resource_group_name
  azure_tenant_id     = var.azure_tenant_id
  azure_object_id     = var.azure_object_id
  subnet_id           = module.virtual_network.container_apps_subnet_id
}


module "public_ip" {
  source              = "../../modules/public_ip"
  name                = "gateway-frontend-ip"
  resource_group_name = module.resource_group.resource_group_name
}

module "application_gateway" {
  source                    = "../../modules/application_gateway"
  resource_group_name       = module.resource_group.resource_group_name
  container_app_subnet_id   = module.virtual_network.container_apps_subnet_id
  gateway_subnet_id         = module.virtual_network.gateway_subnet_id
  backend_address           = "backend.${module.container_apps_env.container_app_environment_default_domain}"
  ui_address                = "frontend.${module.container_apps_env.container_app_environment_default_domain}"
  gateway_public_ip_id      = module.public_ip.public_ip_id
  react_app_address         = "ui.${module.container_apps_env.container_app_environment_default_domain}"
  ssl_certificate_file_path = var.ssl_certificate_file_path
  ssl_certificate_password  = var.ssl_certificate_password
  host_name                 = var.host_name
}

module "private_dns_zone" {
  source                               = "../../modules/private_dns_zone"
  resource_group_name                  = module.resource_group.resource_group_name
  private_dns_zone_name                = module.container_apps_env.container_app_environment_default_domain
  virtual_network_id                   = module.virtual_network.virtual_network_id
  container_apps_environment_static_ip = module.container_apps_env.container_app_environment_static_ip
}

module "container_app_backend" {
  source                      = "../../modules/container_apps/backend"
  resource_group_name         = module.resource_group.resource_group_name
  container_app_env_id        = module.container_apps_env.container_app_environment_id
  docker_image                = format("%s/%s", var.container_registry_server, "tallulah/backend:v0.1.0_dc1a28d")
  container_registry_server   = var.container_registry_server
  container_registry_username = var.container_registry_username
  container_registry_password = var.container_registry_password
  azure_client_id             = var.azure_client_id
  azure_client_secret         = var.azure_client_secret
  azure_tenant_id             = var.azure_tenant_id
  keyvault_url                = module.keyvault.keyvault_url
  jwt_secret                  = var.jwt_secret
  mongo_connection_url        = var.mongo_connection_url
  outlook_client_id           = var.outlook_client_id
  outlook_client_secret       = var.outlook_client_secret
  outlook_tenant_id           = var.outlook_tenant_id
  outlook_redirect_uri        = var.outlook_redirect_uri
  password_pepper             = var.password_pepper
  rabbit_mq_host              = var.rabbit_mq_host
  refresh_secret              = var.refresh_secret
  storage_container_sas_url   = var.storage_container_sas_url
  tallulah_admin_password     = var.tallulah_admin_password
  storage_account_connection_string = var.storage_account_connection_string
  elastic_cloud_id = var.elastic_cloud_id
  elastic_password = var.elastic_password
}

module "container_app_rabbit_mq" {
  source                      = "../../modules/container_apps/rabbit_mq"
  resource_group_name         = module.resource_group.resource_group_name
  container_app_env_id        = module.container_apps_env.container_app_environment_id
  docker_image                = format("%s/%s", var.container_registry_server, "tallulah/rabbitmq:v0.1.0_dc1a28d")
  container_registry_server   = var.container_registry_server
  container_registry_username = var.container_registry_username
  container_registry_password = var.container_registry_password
  rabbit_mq_password          = var.rabbit_mq_password
  rabbit_mq_user              = var.rabbit_mq_user
}

module "container_app_classifier" {
  source                      = "../../modules/container_apps/classifier"
  resource_group_name         = module.resource_group.resource_group_name
  container_app_env_id        = module.container_apps_env.container_app_environment_id
  docker_image                = format("%s/%s", var.container_registry_server, "tallulah/classifier:v0.1.0_8792737")
  container_registry_server   = var.container_registry_server
  container_registry_username = var.container_registry_username
  container_registry_password = var.container_registry_password
  mongo_connection_url        = var.mongo_connection_url
  rabbit_mq_host              = var.rabbit_mq_host
}


module "container_app_frontend" {
  source                      = "../../modules/container_apps/frontend"
  resource_group_name         = module.resource_group.resource_group_name
  container_app_env_id        = module.container_apps_env.container_app_environment_id
  docker_image                = format("%s/%s", var.container_registry_server, "tallulah/ui:v0.1.0_f64fefd")
  container_registry_server   = var.container_registry_server
  container_registry_username = var.container_registry_username
  container_registry_password = var.container_registry_password
}


module "container_app_logstash" {
  source                      = "../../modules/container_apps/logstash"
  resource_group_name         = module.resource_group.resource_group_name
  container_app_env_id        = module.container_apps_env.container_app_environment_id
  docker_image                = format("%s/%s", var.container_registry_server, "tallulah/logstash:v0.1.0_dc1a28d")
  container_registry_server   = var.container_registry_server
  container_registry_username = var.container_registry_username
  container_registry_password = var.container_registry_password
  elastic_cloud_username      = var.elastic_cloud_username
  elastic_cloud_password      = var.elastic_cloud_password
  elastic_cloud_host          = var.elastic_cloud_host
}


module "storage_account" {
  source              = "../../modules/storage_account"
  name                = "tallulahstorage"
  resource_group_name = module.resource_group.resource_group_name
}
