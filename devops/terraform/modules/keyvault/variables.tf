variable "resource_group_name" {
  description = "The name of the resource group"
  type        = string
}

variable "keyvault_name" {
  description = "Name of the Key Vault"
  type = string
}

variable "azure_tenant_id" {
  description = "Azure Tenant ID which will have access to the Key Vault"
  type = string
}

variable "azure_object_id" {
  description = "Azure Service Principal which will have access to the Key Vault"
  type = string
}

variable "subnet_id" {
  description = "Subnet ID which will have access to the Key Vault"
  type = string
}
