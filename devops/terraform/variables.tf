variable "azure_subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

variable "resource_group_name" {
  description = "Azure Resource Group name"
  type        = string
}

variable "container_registry_server" {
  description = "Container registry server"
  type        = string
}

variable "host_name" {
  description = "Host name that the application gateway will listen to"
  type        = string
}

variable "host_name_2" {
  description = "Host name that the application gateway will listen to"
  type        = string
}

variable "backend_container_image_tag" {
  description = "The tag of the backend container image"
  type        = string
}

variable "ui_container_image_tag" {
  description = "The tag of the frontend container image"
  type        = string
}

variable "rabbitmq_container_image_tag" {
  description = "The tag of the rabbitmq container image"
  type        = string
}

variable "logstash_container_image_tag" {
  description = "The tag of the logstash container image"
  type        = string

}

variable "classifier_container_image_tag" {
  description = "The tag of the classifier container image"
  type        = string
}

variable "devops_keyvault_name" {
  description = "The name of the keyvault"
  type        = string
}

variable "devops_keyvault_url" {
  description = "The URL of the keyvault"
  type        = string
}

variable "devops_resource_group_name" {
  description = "The name of the resource group"
  type        = string
}
