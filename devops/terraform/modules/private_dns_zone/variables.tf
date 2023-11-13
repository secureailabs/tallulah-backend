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
    default     = "proudglacier-f81badf3.westus.azurecontainerapps.io"
}
