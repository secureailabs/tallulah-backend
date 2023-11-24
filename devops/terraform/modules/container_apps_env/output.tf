output "container_app_environment_name" {
  value = azurerm_container_app_environment.container_app_environment.name
}

output "container_app_environment_default_domain" {
  value = azurerm_container_app_environment.container_app_environment.default_domain
}

output "container_app_environment_static_ip" {
  value = azurerm_container_app_environment.container_app_environment.static_ip_address
}

output "container_app_environment_id" {
  value = azurerm_container_app_environment.container_app_environment.id
}
