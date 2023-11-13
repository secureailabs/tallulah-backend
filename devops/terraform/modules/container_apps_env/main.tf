
resource "azurerm_container_app_environment" "container_app_environment" {
  infrastructure_subnet_id       = var.infrastructure_subnet_id
  internal_load_balancer_enabled = true
  location                       = "westus"
  log_analytics_workspace_id     = null
  name                           = var.name
  resource_group_name            = var.resource_group_name
}
