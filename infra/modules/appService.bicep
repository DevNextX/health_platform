param environmentName string
param location string

@description('App Service Plan name.')
param planName string

@description('Web App name (must be globally unique).')
param webAppName string

@description('App Service Plan SKU name (e.g. B1, S1).')
param skuName string = 'B1'

@description('ACR resource ID.')
param acrId string

@description('ACR login server (e.g. myacr.azurecr.io).')
param acrLoginServer string

@description('Full container image reference (e.g. myacr.azurecr.io/repo:tag).')
param containerImage string

@description('Application Insights connection string.')
param appInsightsConnectionString string

var tags = {
  'azd-env-name': environmentName
  'azd-service-name': 'api'
}

resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: take('id-api-${environmentName}-${uniqueString(resourceGroup().id)}', 128)
  location: location
  tags: tags
}

resource plan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: planName
  location: location
  kind: 'linux'
  tags: {
    'azd-env-name': environmentName
  }
  sku: {
    name: skuName
  }
  properties: {
    reserved: true
  }
}

resource webApp 'Microsoft.Web/sites@2022-03-01' = {
  name: webAppName
  location: location
  kind: 'app,linux,container'
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${uami.id}': {}
    }
  }
  properties: {
    httpsOnly: true
    serverFarmId: plan.id
    siteConfig: {
      linuxFxVersion: 'DOCKER|${containerImage}'
      alwaysOn: true
      ftpsState: 'Disabled'

      // Critical: acrUserManagedIdentityID expects the *clientId* of a user-assigned managed identity.
      // Do NOT pass the identity resourceId here.
      acrUseManagedIdentityCreds: true
      acrUserManagedIdentityID: uami.properties.clientId

      appSettings: [
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
        {
          name: 'DOCKER_REGISTRY_SERVER_URL'
          value: 'https://${acrLoginServer}'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsightsConnectionString
        }
        {
          name: 'PORT'
          value: '8000'
        }
        {
          name: 'FLASK_APP'
          value: 'src.app'
        }
        {
          name: 'SQLALCHEMY_DATABASE_URI'
          value: 'sqlite:///instance/health_platform.db'
        }
        {
          name: 'JWT_SECRET_KEY'
          value: uniqueString(resourceGroup().id, webAppName)
        }
        {
          name: 'CORS_ORIGINS'
          value: 'https://${webAppName}.azurewebsites.net'
        }
      ]
    }
  }
}

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: last(split(acrId, '/'))
}

var acrPullRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')

resource acrPullAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, uami.id, acrPullRoleDefinitionId)
  scope: acr
  properties: {
    roleDefinitionId: acrPullRoleDefinitionId
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

output webAppName string = webApp.name
output endpointUrl string = 'https://${webApp.properties.defaultHostName}'
output identityClientId string = uami.properties.clientId
output identityPrincipalId string = uami.properties.principalId
