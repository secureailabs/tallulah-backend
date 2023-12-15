variable "azure_tenant_id" {
  description = "Azure Tenant ID which will have access to the Key Vault"
  type        = string
}

variable "azure_object_id" {
  description = "Azure Service Principal which will have access to the Key Vault"
  type        = string
}

variable "azure_client_id" {
  description = "Azure service principal client ID"
  type        = string
}

variable "azure_client_secret" {
  description = "Azure service principal client secret"
  type        = string
}

variable "azure_subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

variable "container_registry_password" {
  description = "Container registry password"
  type        = string
}

variable "container_registry_server" {
  description = "Container registry server"
  type        = string
}

variable "container_registry_username" {
  description = "Container registry username"
  type        = string
}

variable "jwt_secret" {
  description = "JWT secret"
  type        = string
}

variable "mongo_connection_url" {
  description = "Mongodb connection url"
  type        = string
}

variable "outlook_client_id" {
  description = "Outlook client ID for mail integration"
  type        = string
}

variable "outlook_client_secret" {
  description = "Outlook client secret for mail integration"
  type        = string
}

variable "outlook_redirect_uri" {
  description = "Outlook redirect URI for mail integration"
  type        = string
}

variable "outlook_tenant_id" {
  description = "Outlook tenant ID for mail integration"
  type        = string
}

variable "password_pepper" {
  description = "Password pepper"
  type        = string
}

variable "rabbit_mq_host" {
  description = "RabbitMQ host"
  type        = string
}

variable "rabbit_mq_password" {
  description = "RabbitMQ password"
  type        = string
}

variable "rabbit_mq_user" {
  description = "RabbitMQ user"
  type        = string
}

variable "refresh_secret" {
  description = "Refresh secret"
  type        = string
}

variable "storage_container_sas_url" {
  description = "Storage container SAS URL"
  type        = string
}

variable "tallulah_admin_password" {
  description = "Tallulah admin password"
  type        = string
}

variable "godaddy_secret" {
  description = "value of godaddy secret"
  type        = string
}

variable "godaddy_key" {
  description = "value of godaddy key"
  type        = string
}

variable "google_domains_token" {
  description = "value of google domains token"
  type        = string
}

variable "ssl_certificate_file_path" {
  description = "SSL certificate file path"
  type        = string
}

variable "ssl_certificate_password" {
  description = "SSL certificate password"
  type        = string
}

variable "host_name" {
  description = "Host name that the application gateway will listen to"
  type        = string
}

variable "elastic_cloud_username" {
  description = "The username of the Elastic Cloud"
  type        = string
}

variable "elastic_cloud_password" {
  description = "The password of the Elastic Cloud"
  type        = string
}

variable "elastic_cloud_host" {
  description = "The URL of the Elastic Cloud"
  type        = string
}
