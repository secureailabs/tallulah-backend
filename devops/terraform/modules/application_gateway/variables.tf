variable "resource_group_name" {
  description = "The name of the resource group"
  type        = string
}

variable "infrastructure_subnet_id" {
  description = "The ID of the infrastructure subnet"
  type        = string
}

variable "gateway_subnet_id" {
  description = "The ID of the gateway subnet"
  type        = string
}

variable "backend_address" {
  description = "The backend address"
  type        = string
}
