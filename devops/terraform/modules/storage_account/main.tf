resource "random_string" "storage_account_name_postfix" {
  length  = 5
  lower   = true
  numeric = false
  special = false
  upper   = false
}

resource "azurerm_storage_account" "storage_account" {
  name                = "${var.name}${random_string.storage_account_name_postfix.result}"
  resource_group_name = var.resource_group_name

  location                         = "westus"
  account_kind                     = "StorageV2"
  account_tier                     = "Standard"
  account_replication_type         = "LRS"
  public_network_access_enabled    = true
  cross_tenant_replication_enabled = true
  blob_properties {
    cors_rule {
      allowed_headers    = ["*"]
      allowed_methods    = ["GET", "DELETE", "HEAD", "MERGE", "POST", "OPTIONS", "PUT", "PATCH"]
      allowed_origins    = ["*"]
      exposed_headers    = [""]
      max_age_in_seconds = 0
    }
  }
}

resource "azurerm_storage_container" "blob_container" {
  name                  = "logos"
  container_access_type = "blob"
  storage_account_name  = azurerm_storage_account.storage_account.name
}

resource "azurerm_storage_container" "image_container" {
  name                  = "form-image"
  container_access_type = "private"
  storage_account_name  = azurerm_storage_account.storage_account.name
}

resource "azurerm_storage_container" "video_container" {
  name                  = "form-video"
  container_access_type = "private"
  storage_account_name  = azurerm_storage_account.storage_account.name
}

resource "azurerm_storage_container" "file_container" {
  name                  = "form-file"
  container_access_type = "private"
  storage_account_name  = azurerm_storage_account.storage_account.name
}

resource "azurerm_storage_container" "concent_container" {
  name                  = "form-concent"
  container_access_type = "blob"
  storage_account_name  = azurerm_storage_account.storage_account.name
}
