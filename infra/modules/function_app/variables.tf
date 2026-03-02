variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "function_app_name" {
  type = string
}

variable "resource_prefix" {
  type = string
}

variable "tags" {
  type = map(string)
}

variable "appinsights_connection_string" {
  type      = string
  sensitive = true
}

variable "appinsights_instrumentation_key" {
  type      = string
  sensitive = true
}

variable "model_endpoint" {
  type      = string
  sensitive = true
}

variable "model_api_key" {
  type      = string
  sensitive = true
}

variable "model_name" {
  type = string
}

variable "github_token" {
  type      = string
  sensitive = true
}

variable "github_repo" {
  type = string
}

variable "github_branch" {
  type = string
}
