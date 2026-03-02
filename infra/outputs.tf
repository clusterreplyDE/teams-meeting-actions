output "resource_group_name" {
  description = "Name of the resource group"
  value       = data.azurerm_resource_group.main.name
}

output "function_app_name" {
  description = "Name of the Function App"
  value       = module.function_app.function_app_name
}

output "function_app_url" {
  description = "Default hostname of the Function App"
  value       = module.function_app.function_app_url
}

output "appinsights_name" {
  description = "Application Insights resource name"
  value       = module.monitoring.appinsights_name
}
