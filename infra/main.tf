locals {
  resource_prefix = "${var.project_name}-${var.environment}"
  tags = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
  }
}

data "azurerm_resource_group" "main" {
  name = var.resource_group_name
}

module "monitoring" {
  source = "./modules/monitoring"

  resource_group_name = data.azurerm_resource_group.main.name
  location            = data.azurerm_resource_group.main.location
  resource_prefix     = local.resource_prefix
  tags                = local.tags
}

module "function_app" {
  source = "./modules/function_app"

  resource_group_name          = data.azurerm_resource_group.main.name
  location                     = data.azurerm_resource_group.main.location
  function_app_name            = var.function_app_name
  resource_prefix              = local.resource_prefix
  tags                         = local.tags
  appinsights_connection_string = module.monitoring.appinsights_connection_string
  appinsights_instrumentation_key = module.monitoring.appinsights_instrumentation_key

  model_endpoint = var.model_endpoint
  model_api_key  = var.model_api_key
  model_name     = var.model_name
  github_token    = var.github_token
  github_repo     = var.github_repo
  github_branch   = var.github_branch
}
