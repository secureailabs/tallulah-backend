variable "azure_client_id" {
  description = "The ID of the Azure client"
  type        = string
}

variable "azure_client_secret" {
  description = "The secret of the Azure client"
  type        = string
}

variable "azure_tenant_id" {
  description = "The ID of the Azure tenant"
  type        = string
}

variable "devops_keyvault_url" {
  description = "The URL of the devops keyvault"
  type        = string
}

variable "resource_group_name" {
  description = "The name of the resource group"
  type        = string
}

variable "container_app_env_id" {
  description = "The ID of the container app environment"
  type        = string
}

variable "mongo_connection_url" {
  description = "The connection URL of the MongoDB instance"
  type        = string
}

variable "rabbit_mq_host" {
  description = "The host of the RabbitMQ instance"
  type        = string
}

variable "docker_image" {
  description = "The url of the Docker image"
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

variable "container_registry_password" {
  description = "The password of the container registry"
  type        = string
}

