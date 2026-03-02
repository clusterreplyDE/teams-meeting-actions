resource "azurerm_storage_account" "func" {
  name                     = replace("st${var.resource_prefix}", "-", "")
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  tags                     = var.tags
}

resource "azurerm_service_plan" "func" {
  name                = "asp-${var.resource_prefix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = "Linux"
  sku_name            = "Y1"
  tags                = var.tags
}

resource "azurerm_linux_function_app" "main" {
  name                       = var.function_app_name
  resource_group_name        = var.resource_group_name
  location                   = var.location
  service_plan_id            = azurerm_service_plan.func.id
  storage_account_name       = azurerm_storage_account.func.name
  storage_account_access_key = azurerm_storage_account.func.primary_access_key
  tags                       = var.tags

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME"           = "python"
    "APPINSIGHTS_INSTRUMENTATIONKEY"     = var.appinsights_instrumentation_key
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = var.appinsights_connection_string
    "MODEL_ENDPOINT"                     = var.model_endpoint
    "MODEL_API_KEY"                      = var.model_api_key
    "MODEL_NAME"                         = var.model_name
    "GITHUB_TOKEN"                       = var.github_token
    "GITHUB_REPO"                        = var.github_repo
    "GITHUB_BRANCH"                      = var.github_branch
  }
}
