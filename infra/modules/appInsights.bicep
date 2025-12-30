param name string
param location string

@description('Resource ID of the Log Analytics workspace for workspace-based Application Insights.')
param workspaceResourceId string

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: name
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: workspaceResourceId
  }
}

output resourceId string = appInsights.id
output connectionString string = appInsights.properties.ConnectionString
