resource "azurerm_public_ip" "public_ip" {
  allocation_method   = "Static"
  location            = "westus"
  name                = var.name
  resource_group_name = var.resource_group_name
  sku                 = "Standard"
}
