targetScope = 'resourceGroup'

@description('Deployment location. Defaults to the resource group location.')
param location string = resourceGroup().location

@description('azd environment name (e.g. dev).')
param environmentName string = 'dev'

@description('A short, lowercase, alphanumeric prefix used for global resource names (ACR/WebApp).')
param namePrefix string = 'healthplatform'

@allowed([
  'Basic'
  'Standard'
  'Premium'
])
@description('Azure Container Registry SKU.')
param acrSku string = 'Basic'

@description('App Service Plan SKU name (e.g. B1, S1).')
param appServicePlanSkuName string = 'B1'

@description('Container image name (repository) without registry hostname.')
param containerImageName string = 'health-platform-backend'

@description('Container image tag. Typically set to the git SHA in CI.')
param containerImageTag string = 'latest'

@description('Log Analytics retention in days.')
param logAnalyticsRetentionInDays int = 30

var uniqueSuffix = toLower(uniqueString(resourceGroup().id))
var normalizedPrefix = toLower(replace(replace(namePrefix, '-', ''), '_', ''))

var acrName = take('${normalizedPrefix}${environmentName}${uniqueSuffix}', 50)
var logAnalyticsName = take('log-${normalizedPrefix}-${environmentName}-${uniqueSuffix}', 63)
var appInsightsName = take('appi-${normalizedPrefix}-${environmentName}-${uniqueSuffix}', 63)
var appServicePlanName = take('asp-${normalizedPrefix}-${environmentName}-${uniqueSuffix}', 40)
var webAppName = take('app-${normalizedPrefix}-${environmentName}-${uniqueSuffix}', 60)

module logAnalytics 'modules/logAnalytics.bicep' = {
  name: 'logAnalytics'
  params: {
    name: logAnalyticsName
    location: location
    retentionInDays: logAnalyticsRetentionInDays
  }
}

module appInsights 'modules/appInsights.bicep' = {
  name: 'appInsights'
  params: {
    name: appInsightsName
    location: location
    workspaceResourceId: logAnalytics.outputs.workspaceId
  }
}

module acr 'modules/acr.bicep' = {
  name: 'acr'
  params: {
    name: acrName
    location: location
    sku: acrSku
  }
}

var fullContainerImage = '${acr.outputs.loginServer}/${containerImageName}:${containerImageTag}'

module appService 'modules/appService.bicep' = {
  name: 'appService'
  params: {
    environmentName: environmentName
    location: location
    planName: appServicePlanName
    webAppName: webAppName
    skuName: appServicePlanSkuName
    acrId: acr.outputs.resourceId
    acrLoginServer: acr.outputs.loginServer
    containerImage: fullContainerImage
    appInsightsConnectionString: appInsights.outputs.connectionString
  }
}

output AZURE_LOCATION string = location
output AZURE_RESOURCE_GROUP string = resourceGroup().name

output AZURE_CONTAINER_REGISTRY_NAME string = acr.outputs.name
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = acr.outputs.loginServer

output AZURE_WEBAPP_NAME string = appService.outputs.webAppName
output SERVICE_API_ENDPOINT_URL string = appService.outputs.endpointUrl
