resource "azurerm_web_application_firewall_policy" "web_application_firewall_policy" {
  location            = "westus"
  name                = "waf-policy"
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

resource "azurerm_application_gateway" "application_gateway" {
  enable_http2        = true
  firewall_policy_id  = azurerm_web_application_firewall_policy.web_application_firewall_policy.id
  location            = "westus"
  name                = "app-gateway"
  resource_group_name = var.resource_group_name
  autoscale_configuration {
    max_capacity = 10
    min_capacity = 0
  }
  private_link_configuration {
    name = "app-gateway-private-link"
    ip_configuration {
      name                          = "private-link-ip-config"
      primary                       = false
      private_ip_address_allocation = "Dynamic"
      subnet_id                     = var.container_app_subnet_id
    }
  }
  frontend_ip_configuration {
    name                            = "appGwPublicFrontendIpIPv4"
    private_link_configuration_name = "app-gateway-private-link"
    public_ip_address_id            = var.gateway_public_ip_id
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
    name                           = "app-gateway-listener"
    frontend_ip_configuration_name = "appGwPublicFrontendIpIPv4"
    frontend_port_name             = "port_80"
    protocol                       = "Http"
  }
  request_routing_rule {
    name                       = "app-gateway-routing-rule"
    backend_address_pool_name  = "app-gateway-backend-pool"
    backend_http_settings_name = "app-gateway-backend-setting"
    http_listener_name         = "app-gateway-listener"
    priority                   = 1
    rule_type                  = "Basic"
  }
  backend_address_pool {
    name  = "app-gateway-backend-pool"
    fqdns = [var.backend_address]
  }
  backend_http_settings {
    name                                = "app-gateway-backend-setting"
    cookie_based_affinity               = "Disabled"
    pick_host_name_from_backend_address = true
    port                                = 443
    protocol                            = "Https"
    request_timeout                     = 20
  }
  sku {
    name = "WAF_v2"
    tier = "WAF_v2"
  }
}
