variable "resource_group_name" {
  description = "The name of the resource group"
  type        = string
}

variable "name" {
  description = "The name of the container app environment"
  type        = string
}

variable "infrastructure_subnet_id" {
  description = "The ID of the infrastructure subnet"
  type        = string
}
