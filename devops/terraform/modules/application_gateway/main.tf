resource "azurerm_web_application_firewall_policy" "web_application_firewall_policy" {
  location            = "westus"
  name                = "my-waf-policy"
  resource_group_name = var.resource_group_name
  managed_rules {
    managed_rule_set {
      version = "3.2"
    }
  }
  policy_settings {
    mode = "Detection"
  }
}

resource "azurerm_public_ip" "public_ip" {
  allocation_method   = "Static"
  location            = "westus"
  name                = "frontend-ui"
  resource_group_name = var.resource_group_name
  sku                 = "Standard"
}

resource "azurerm_application_gateway" "application_gateway" {
  enable_http2        = true
  firewall_policy_id  = azurerm_web_application_firewall_policy.web_application_firewall_policy.id
  location            = "westus"
  name                = "tallulah-gateway"
  resource_group_name = var.resource_group_name
  autoscale_configuration {
    max_capacity = 10
    min_capacity = 0
  }
  backend_address_pool {
    fqdns = [var.backend_address]
    name  = "tallulah-backend-pool"
  }
  backend_http_settings {
    cookie_based_affinity               = "Disabled"
    name                                = "my-agw-backend-setting"
    pick_host_name_from_backend_address = true
    port                                = 443
    protocol                            = "Https"
    request_timeout                     = 20
  }
  frontend_ip_configuration {
    name                            = "appGwPublicFrontendIpIPv4"
    private_link_configuration_name = "my-agw-private-link"
    public_ip_address_id            = azurerm_public_ip.public_ip.id
  }
  frontend_port {
    name = "port_80"
    port = 80
  }
  gateway_ip_configuration {
    name      = "appGatewayIpConfig"
    subnet_id = var.gateway_subnet_id
  }
  http_listener {
    frontend_ip_configuration_name = "appGwPublicFrontendIpIPv4"
    frontend_port_name             = "port_80"
    name                           = "my-agw-listener"
    protocol                       = "Http"
  }
  private_link_configuration {
    name = "my-agw-private-link"
    ip_configuration {
      name                          = "privateLinkIpConfig1"
      primary                       = false
      private_ip_address_allocation = "Dynamic"
      subnet_id                     = var.infrastructure_subnet_id
    }
  }
  request_routing_rule {
    backend_address_pool_name  = "tallulah-backend-pool"
    backend_http_settings_name = "my-agw-backend-setting"
    http_listener_name         = "my-agw-listener"
    name                       = "my-agw-routing-rule"
    priority                   = 1
    rule_type                  = "Basic"
  }
  sku {
    name = "WAF_v2"
    tier = "WAF_v2"
  }
}
