module "resource_group" {
  source                        = "./modules/resource_group"
  resource_group_name_prefix    = "myResourceGroup"
  resource_group_location       = "westus"
}

module "virtual_network" {
  source                        = "./modules/virtual_network"
  resource_group_name           = module.resource_group.resource_group_name
  virtual_network_name          = "tallulah-vnet"
}

module "container_apps_env" {
  source                        = "./modules/container_apps_env"
  resource_group_name           = module.resource_group.resource_group_name
  name                          = "tallulah-env"
  infrastructure_subnet_id      = module.virtual_network.container_apps_subnet_id
}

module "keyvault" {
  source                       = "./modules/keyvault"
  resource_group_name          = module.resource_group.resource_group_name
  keyvault_name                = "tallulah-keyvault"
  azure_tenant_id              = var.azure_tenant_id
  azure_object_id              = var.azure_object_id
  subnet_id                    = module.virtual_network.container_apps_subnet_id
}

module "application_gateway" {
  source                        = "./modules/application_gateway"
  resource_group_name           = module.resource_group.resource_group_name
  infrastructure_subnet_id      = module.virtual_network.container_apps_subnet_id
  gateway_subnet_id             = module.virtual_network.gateway_subnet_id
  backend_address               = module.container_apps_env.container_app_environment_default_domain
}

module "private_dns_zone" {
  source                        = "./modules/private_dns_zone"
  resource_group_name           = module.resource_group.resource_group_name
  private_dns_zone_name         = module.container_apps_env.container_app_environment_default_domain
  virtual_network_id            = module.virtual_network.virtual_network_id
}
