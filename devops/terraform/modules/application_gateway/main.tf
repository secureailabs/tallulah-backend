# Using the Azure Application Gateway with a public IP even though the access is only via private IP addresses.
# All the public access is done via DNAT to the private IP addresses from the public IP address.
# Azure Application Gateway does not support Application Gateway without Public IP

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
    min_capacity = 1
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
  private_link_configuration {
    name = "app-gateway-private-link-private-ip"
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
  frontend_ip_configuration {
    # Application Gateway with SKU tier WAF_v2 can only use PrivateIPAddress with IpAllocationMethod as Static.
    name                            = "appGwPrivateFrontendIpIPv4"
    private_link_configuration_name = "app-gateway-private-link-private-ip"
    subnet_id                       = var.gateway_subnet_id
    private_ip_address_allocation   = "Static"
    private_ip_address              = "10.0.16.250"
  }
  frontend_port {
    name = "port_443"
    port = 443
  }
  gateway_ip_configuration {
    name      = "appGatewayIpConfig"
    subnet_id = var.gateway_subnet_id
  }
  ssl_certificate {
    name     = "app-gateway-ssl-cert"
    data     = var.ssl_certificate_pfx
    password = var.ssl_certificate_password
  }
  ssl_certificate {
    name     = "app-gateway-ssl-cert-2"
    data     = var.ssl_certificate_pfx_2
    password = var.ssl_certificate_password
  }
  ssl_profile {
    name = "secure_ssl_profile"
    ssl_policy {
      policy_name          = "AppGwSslPolicy20220101"
      policy_type          = "Predefined"
      min_protocol_version = "TLSv1_2"
    }
  }
  rewrite_rule_set {
    name = "security-headers"

    rewrite_rule {
      name          = "security-headers-rewrite-rule"
      rule_sequence = 1

      # TODO: this will stop the forms being used as iframes in other sites
      # response_header_configuration {
      #   header_name  = "X-Frame-Options"
      #   header_value = "SAMEORIGIN"
      # }
      response_header_configuration {
        header_name  = "Strict Transport Security"
        header_value = "max-age=31536000; includeSubDomains"
      }
    }
  }

  http_listener {
    name                           = "app-gateway-listener"
    frontend_ip_configuration_name = "appGwPrivateFrontendIpIPv4"
    frontend_port_name             = "port_443"
    protocol                       = "Https"
    ssl_certificate_name           = "app-gateway-ssl-cert"
    ssl_profile_name               = "secure_ssl_profile"
    host_name                      = var.host_name
  }
  http_listener {
    name                           = "app-gateway-listener-2"
    frontend_ip_configuration_name = "appGwPrivateFrontendIpIPv4"
    frontend_port_name             = "port_443"
    protocol                       = "Https"
    ssl_certificate_name           = "app-gateway-ssl-cert-2"
    ssl_profile_name               = "secure_ssl_profile"
    host_name                      = var.host_name_2
  }
  # Add an HTTP listener for port 80
  http_listener {
    name                           = "app-gateway-listener-http"
    frontend_ip_configuration_name = "appGwPrivateFrontendIpIPv4"
    frontend_port_name             = "port_80"
    protocol                       = "Http"
    host_name                      = var.host_name
  }
  redirect_configuration {
    name                 = "http-to-https-redirect"
    redirect_type        = "Permanent"
    target_listener_name = "app-gateway-listener"
    include_path         = true
    include_query_string = true
  }
  url_path_map {
    name                               = "app-gateway-url-path-map"
    default_backend_address_pool_name  = "app-gateway-ui-pool"
    default_backend_http_settings_name = "app-gateway-backend-setting"
    path_rule {
      name                       = "app-gateway-path-rule-1"
      paths                      = ["/*"]
      backend_address_pool_name  = "app-gateway-ui-pool"
      backend_http_settings_name = "app-gateway-ui-setting"
    }
    path_rule {
      name                       = "app-gateway-path-rule-2"
      paths                      = ["/api/*"]
      backend_address_pool_name  = "app-gateway-backend-pool"
      backend_http_settings_name = "app-gateway-backend-setting"
    }
  }
  request_routing_rule {
    name                  = "app-gateway-routing-rule"
    http_listener_name    = "app-gateway-listener"
    priority              = 1
    rule_type             = "PathBasedRouting"
    url_path_map_name     = "app-gateway-url-path-map"
    rewrite_rule_set_name = "security-headers"
  }
  request_routing_rule {
    name                  = "app-gateway-routing-rule-2"
    http_listener_name    = "app-gateway-listener-2"
    priority              = 2
    rule_type             = "PathBasedRouting"
    url_path_map_name     = "app-gateway-url-path-map"
    rewrite_rule_set_name = "security-headers"
  }
  request_routing_rule {
    name                        = "app-gateway-http-redirect-rule"
    http_listener_name          = "app-gateway-listener-http"
    rule_type                   = "Basic"
    redirect_configuration_name = "http-to-https-redirect"
    priority                    = 3
  }
  backend_address_pool {
    name  = "app-gateway-backend-pool"
    fqdns = [var.backend_address]
  }
  backend_address_pool {
    name  = "app-gateway-ui-pool"
    fqdns = [var.ui_address]
  }
  backend_http_settings {
    name                                = "app-gateway-backend-setting"
    cookie_based_affinity               = "Disabled"
    pick_host_name_from_backend_address = true
    port                                = 8000
    protocol                            = "Http"
    request_timeout                     = 20
  }
  backend_http_settings {
    name                                = "app-gateway-ui-setting"
    cookie_based_affinity               = "Disabled"
    pick_host_name_from_backend_address = true
    port                                = 500
    protocol                            = "Http"
    request_timeout                     = 20
  }
  sku {
    name = "WAF_v2"
    tier = "WAF_v2"
  }
}
