module "development" {
  source                      = "./environments/development"
  azure_tenant_id             = var.azure_tenant_id
  azure_object_id             = var.azure_object_id
  azure_client_id             = var.azure_client_id
  azure_client_secret         = var.azure_client_secret
  container_registry_password = var.container_registry_password
  container_registry_server   = var.container_registry_server
  container_registry_username = var.container_registry_username
  jwt_secret                  = var.jwt_secret
  refresh_secret              = var.refresh_secret
  password_pepper             = var.password_pepper
  tallulah_admin_password     = var.tallulah_admin_password
  mongo_connection_url        = var.mongo_connection_url
  outlook_client_id           = var.outlook_client_id
  outlook_client_secret       = var.outlook_client_secret
  outlook_redirect_uri        = var.outlook_redirect_uri
  outlook_tenant_id           = var.outlook_tenant_id
  rabbit_mq_host              = var.rabbit_mq_host
  rabbit_mq_password          = var.rabbit_mq_password
  rabbit_mq_user              = var.rabbit_mq_user
  storage_container_sas_url   = var.storage_container_sas_url
  ssl_certificate_file_path   = var.ssl_certificate_file_path
  ssl_certificate_password    = var.ssl_certificate_password
  host_name                   = var.host_name
}


module "tls_certificates" {
  source                   = "./modules/tls_certificate"
  godaddy_api_key          = var.godaddy_key
  godaddy_api_secret       = var.godaddy_secret
  google_domains_token     = var.google_domains_token
  ssl_certificate_password = var.ssl_certificate_password
}
