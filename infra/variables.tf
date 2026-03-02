variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "swedencentral"
}

variable "resource_group_name" {
  description = "Name of the existing Azure resource group"
  type        = string
  default     = "rg-marco-ai"
}

variable "function_app_name" {
  description = "Name of the Azure Function App"
  type        = string
  default     = "func-teams-ai-agents"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "transcript-helper"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "model_endpoint" {
  description = "AI model endpoint URL (azure-ai-inference compatible)"
  type        = string
  sensitive   = true
}

variable "model_api_key" {
  description = "API key for the model endpoint"
  type        = string
  sensitive   = true
}

variable "model_name" {
  description = "Model name to use for inference"
  type        = string
  default     = "Kimi-K2.5"
}

variable "github_token" {
  description = "GitHub Personal Access Token"
  type        = string
  sensitive   = true
}

variable "github_repo" {
  description = "GitHub repository in owner/repo format"
  type        = string
}

variable "github_branch" {
  description = "GitHub branch to write summaries to"
  type        = string
  default     = "main"
}
