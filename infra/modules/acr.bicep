@description('ACR name (must be globally unique).')
param name string

param location string

@allowed([
  'Basic'
  'Standard'
  'Premium'
])
param sku string = 'Basic'

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: name
  location: location
  sku: {
    name: sku
  }
  properties: {
    adminUserEnabled: false
  }
}

output name string = acr.name
output resourceId string = acr.id
output loginServer string = acr.properties.loginServer
