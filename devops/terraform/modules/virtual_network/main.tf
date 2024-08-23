# 10.0.0.2 - 10.0.255.254
resource "azurerm_virtual_network" "vnet" {
  address_space       = ["10.0.0.0/16"]
  location            = "westus"
  name                = var.virtual_network_name
  resource_group_name = var.resource_group_name
}


# 10.0.0.2 - 10.0.15.254
resource "azurerm_subnet" "container_apps_subnet" {
  address_prefixes                              = ["10.0.0.0/20"]
  name                                          = "default"
  resource_group_name                           = var.resource_group_name
  private_link_service_network_policies_enabled = false
  service_endpoints                             = ["Microsoft.KeyVault", "Microsoft.Storage", "Microsoft.CognitiveServices"]
  virtual_network_name                          = var.virtual_network_name
  depends_on                                    = [azurerm_virtual_network.vnet]
}

# 10.0.16.2 - 10.0.16.254
resource "azurerm_subnet" "gateway_subnet" {
  address_prefixes     = ["10.0.16.0/24"]
  name                 = "gateway"
  resource_group_name  = var.resource_group_name
  virtual_network_name = var.virtual_network_name
  depends_on           = [azurerm_virtual_network.vnet]
}

# TODO: create virtual network peering here. It is difficult as the remote virtual network is in a different subscription.
