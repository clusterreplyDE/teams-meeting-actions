terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }

  backend "azurerm" {
    # Configured via -backend-config in CI/CD pipeline:
    #   resource_group_name  = "<from vars.RESOURCE_GROUP>"
    #   storage_account_name = "<from vars.TF_STATE_STORAGE_ACCOUNT>"
    #   container_name       = "tfstate"
    #   key                  = "transcript-helper.tfstate"
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}
