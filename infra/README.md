# Azure Infrastructure (azd + Bicep)

This folder contains the Azure infrastructure-as-code (IaC) skeleton for Issue #89.

## Structure

- `main.bicep`: root orchestration template
- `modules/acr.bicep`: Azure Container Registry (admin user disabled)
- `modules/logAnalytics.bicep`: Log Analytics Workspace
- `modules/appInsights.bicep`: Application Insights (workspace-based)
- `modules/appService.bicep`: Linux App Service Plan + Web App (custom container) + User Assigned Managed Identity + AcrPull role assignment

## Critical note (ACR pull via Managed Identity)

In `modules/appService.bicep`, the App Service setting `acrUserManagedIdentityID` is set to the **clientId** of the **user-assigned managed identity**.

This is required for App Service to pull images from ACR using managed identity. Do not pass the identity **resourceId**.
