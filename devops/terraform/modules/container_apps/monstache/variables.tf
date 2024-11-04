variable "container_app_env_id" {
  description = "The ID of the container app environment"
  type        = string
}

variable "resource_group_name" {
  description = "The name of the resource group"
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

variable "mongo_url" {
  description = "The URL of the MongoDB"
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

variable "docker_image" {
  description = "The url of the Docker image"
  type        = string
}

variable "monstache_change_stream_ns" {
  description = "The change stream namespace"
  type        = string
}
variable "mongo_certificate" {
  description = "The certificate of the MongoDB"
  type        = string
}
