variable "azure_tenant_id" {
  description = "Azure Tenant ID which will have access to the Key Vault"
  type = string
}

variable "azure_object_id" {
  description = "Azure Service Principal which will have access to the Key Vault"
  type = string
}

