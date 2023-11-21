variable "resource_group_name" {
  description = "The name of the resource group"
  type        = string
}

variable "virtual_network_id" {
    description = "The ID of the virtual network"
    type        = string
}

variable "private_dns_zone_name" {
    description = "The name of the private DNS zone"
    type        = string
}

variable "container_apps_environment_static_ip" {
    description = "The static IP address of the container apps environment"
    type        = string
}