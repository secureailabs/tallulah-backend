resource "azurerm_virtual_network" "vnet" {
  address_space       = ["10.0.0.0/16"]
  location            = "westus"
  name                = var.virtual_network_name
  resource_group_name = var.resource_group_name
}

resource "azurerm_subnet" "gateway_subnet" {
  address_prefixes     = ["10.0.16.0/24"]
  name                 = "GatewaySubnet"
  resource_group_name  = var.resource_group_name
  virtual_network_name = var.virtual_network_name
  depends_on = [
    azurerm_virtual_network.vnet,
  ]
}

resource "azurerm_subnet" "container_apps_subnet" {
  address_prefixes     = ["10.0.0.0/20"]
  name                 = "default"
  resource_group_name  = var.resource_group_name
  service_endpoints    = ["Microsoft.KeyVault", "Microsoft.Storage"]
  virtual_network_name = var.virtual_network_name
  depends_on = [
    azurerm_virtual_network.vnet,
  ]
}
