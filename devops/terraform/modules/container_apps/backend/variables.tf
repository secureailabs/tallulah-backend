variable "resource_group_name" {
  description = "The name of the resource group"
  type        = string
}

variable "container_app_env_id" {
  description = "The ID of the container app environment"
  type        = string
}

variable "azure_client_id" {
  description = "The ID of the Azure client"
  type        = string
}

variable "azure_client_secret" {
  description = "The secret of the Azure client"
  type        = string
}

variable "keyvault_url" {
  description = "The URL of the keyvault"
  type        = string
}

variable "azure_tenant_id" {
  description = "The ID of the Azure tenant"
  type        = string
}

variable "container_registry_password" {
  description = "The password of the container registry"
  type        = string
}

variable "jwt_secret" {
  description = "The JWT secret"
  type        = string
}

variable "mongo_connection_url" {
  description = "The connection URL of the MongoDB instance"
  type        = string
}

variable "outlook_client_id" {
  description = "The ID of the Outlook client"
  type        = string
}

variable "outlook_client_secret" {
  description = "The secret of the Outlook client"
  type        = string
}

variable "password_pepper" {
  description = "The password pepper"
  type        = string
}

variable "rabbit_mq_host" {
  description = "The host of the RabbitMQ instance"
  type        = string
}

variable "refresh_secret" {
  description = "The refresh secret"
  type        = string
}

variable "storage_container_sas_url" {
  description = "The SAS URL of the storage container"
  type        = string
}

variable "tallulah_admin_password" {
  description = "The password of the Tallulah admin"
  type        = string
}

variable "outlook_tenant_id" {
  description = "The ID of the Outlook tenant"
  type        = string
}

variable "docker_image" {
  description = "The url of the Docker image"
  type        = string
}

variable "outlook_redirect_uri" {
  description = "The redirect URI of the Outlook client"
  type        = string
}

variable "container_registry_server" {
  description = "The server of the container registry"
  type        = string
}

variable "container_registry_username" {
  description = "The username of the container registry"
  type        = string
}

variable "storage_account_connection_string" {
  description = "The connection string of the storage account"
  type        = string
}

variable "elastic_password" {
  description = "The password of the Elastic instance"
  type        = string
}

variable "elastic_cloud_id" {
  description = "The ID of the Elastic instance"
  type        = string
}

variable "openai_api_base" {
  description = "value of openai api base"
  type        = string
}

variable "openai_api_key" {
  description = "value of openai api key"
  type        = string
}

variable "email_no_reply_refresh_token" {
  description = "value of email no reply refresh token"
  type        = string
}
