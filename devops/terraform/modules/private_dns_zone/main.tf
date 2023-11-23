resource "azurerm_private_dns_zone" "private_dns_zone" {
  name                = var.private_dns_zone_name
  resource_group_name = var.resource_group_name
}

resource "azurerm_private_dns_a_record" "dns_a_record-1" {
  name                = "*"
  records             = [var.container_apps_environment_static_ip]
  resource_group_name = var.resource_group_name
  ttl                 = 3600
  zone_name           = azurerm_private_dns_zone.private_dns_zone.name
}

resource "azurerm_private_dns_a_record" "dns_a_record-2" {
  name                = "@"
  records             = [var.container_apps_environment_static_ip]
  resource_group_name = var.resource_group_name
  ttl                 = 3600
  zone_name           = azurerm_private_dns_zone.private_dns_zone.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "private_dns_zone_virtual_network_link" {
  name                  = "custom-vnet-pdns-link"
  private_dns_zone_name = azurerm_private_dns_zone.private_dns_zone.name
  resource_group_name   = var.resource_group_name
  virtual_network_id    = var.virtual_network_id
}
