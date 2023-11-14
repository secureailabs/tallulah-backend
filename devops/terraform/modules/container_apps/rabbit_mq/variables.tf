variable "resource_group_name" {
  description = "The name of the resource group"
  type        = string
}

variable "container_app_env_id" {
    description = "The ID of the container app environment"
    type        = string
}

variable "rabbit_mq_user" {
    description = "Rabbit MQ user"
    type = string
}
variable "rabbit_mq_password" {
    description = "Rabbit MQ password"
    type = string
}

variable "docker_image" {
    description = "The url of the Docker image"
    type = string
}

variable "container_registry_server" {
    description = "The server of the container registry"
    type = string
}

variable "container_registry_username" {
    description = "The username of the container registry"
    type = string
}

variable "container_registry_password" {
    description = "The password of the container registry"
    type = string
}

