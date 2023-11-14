variable "azure_tenant_id" {
  description = "Azure Tenant ID which will have access to the Key Vault"
  type = string
  default = "3e74e5ef-7e6a-4cf0-8573-680ca49b64d8"
}

variable "azure_object_id" {
  description = "Azure Service Principal which will have access to the Key Vault"
  type = string
  default = "dda140d1-baeb-42b2-a590-c36911ec0c13"
}

variable "azure_client_id" {
  description = "Azure service principal client ID"
  type = string
}

variable "azure_client_secret" {
  description = "Azure service principal client secret"
  type = string
}

variable "container_registry_password" {
  description = "Container registry password"
  type = string
}

variable "container_registry_server" {
  description = "Container registry server"
  type = string
}

variable "container_registry_username" {
  description = "Container registry username"
  type = string
}

variable "jwt_secret" {
  description = "JWT secret"
  type = string
}

variable "mongo_connection_url" {
  description = "Mongodb connection url"
  type = string
}

variable "outlook_client_id" {
  description = "Outlook client ID for mail integration"
  type = string
}

variable "outlook_client_secret" {
  description = "Outlook client secret for mail integration"
  type = string
}

variable "outlook_redirect_uri" {
  description = "Outlook redirect URI for mail integration"
  type = string
}

variable "outlook_tenant_id" {
  description = "Outlook tenant ID for mail integration"
  type = string
}

variable "password_pepper" {
  description = "Password pepper"
  type = string
}

variable "rabbit_mq_host" {
  description = "RabbitMQ host"
  type = string
}

variable "rabbit_mq_password" {
  description = "RabbitMQ password"
  type = string
}

variable "rabbit_mq_user" {
  description = "RabbitMQ user"
  type = string
}

variable "refresh_secret" {
  description = "Refresh secret"
  type = string
}

variable "storage_container_sas_url" {
  description = "Storage container SAS URL"
  type = string
}

variable "tallulah_admin_password" {
  description = "Tallulah admin password"
  type = string
}