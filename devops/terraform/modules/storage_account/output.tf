output "storage_account_connection_string" {
  value = azurerm_storage_account.storage_account.primary_connection_string
}
