# GitHub Actions Deployment Setup

This repository contains a GitHub Actions workflow that automatically builds and deploys the Health Platform application (Python Flask + React) as a container to Azure App Service.

## Prerequisites

Before the workflow can run successfully, you need to configure the following GitHub secrets and variables.

## Required GitHub Secrets

### 1. Azure OIDC Authentication (Recommended)

The workflow uses **Federated Credentials (OIDC)** for secure authentication without storing long-lived secrets.

#### Create Azure AD App Registration with Federated Credential

```bash
# 1. Create app registration
az ad app create --display-name "github-actions-health-platform"

# Note the appId (client-id) from output
APP_ID="<appId-from-previous-command>"

# 2. Create service principal
az ad sp create --id $APP_ID

# 3. Assign Contributor role to resource group
az role assignment create \
  --assignee $APP_ID \
  --role Contributor \
  --scope /subscriptions/<subscription-id>/resourceGroups/<resource-group-name>

# 4. Assign AcrPush role to ACR
az role assignment create \
  --assignee $APP_ID \
  --role AcrPush \
  --scope /subscriptions/<subscription-id>/resourceGroups/<resource-group-name>/providers/Microsoft.ContainerRegistry/registries/<acr-name>

# 5. Create federated credential for GitHub Actions
az ad app federated-credential create \
  --id $APP_ID \
  --parameters '{
    "name": "github-actions-main",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:<your-github-username>/<your-repo-name>:ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"]
  }'

# 6. Also create credential for pull requests (optional but recommended)
az ad app federated-credential create \
  --id $APP_ID \
  --parameters '{
    "name": "github-actions-pr",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:<your-github-username>/<your-repo-name>:pull_request",
    "audiences": ["api://AzureADTokenExchange"]
  }'
```

#### Add these secrets to GitHub:

1. **AZURE_CLIENT_ID** - The Application (client) ID from app registration
2. **AZURE_TENANT_ID** - Your Azure AD tenant ID
3. **AZURE_SUBSCRIPTION_ID** - Your Azure subscription ID

To find these values:
```bash
# Get tenant ID
az account show --query tenantId -o tsv

# Get subscription ID
az account show --query id -o tsv

# Get client ID (from app registration)
az ad app list --display-name "github-actions-health-platform" --query "[0].appId" -o tsv
```

## Required GitHub Variables

Configure these in **Settings → Secrets and variables → Actions → Variables**:

1. **AZURE_CONTAINER_REGISTRY_NAME** - ACR name (e.g., `crhealthplatformdev123`)
2. **AZURE_APP_SERVICE_NAME** - Web App name (e.g., `app-healthplatform-dev-123`)
3. **AZURE_RESOURCE_GROUP** - Resource group name (e.g., `rg-health-platform-dev`)

To find resource names:
```bash
# List resources in your resource group
az resource list --resource-group <your-rg-name> --output table

# Get ACR name
az acr list --resource-group <your-rg-name> --query "[0].name" -o tsv

# Get App Service name
az webapp list --resource-group <your-rg-name> --query "[0].name" -o tsv
```

## How to Configure Secrets and Variables

### Add Secrets:
1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with the exact name shown above

### Add Variables:
1. Same location as secrets
2. Click the **Variables** tab
3. Click **New repository variable**
4. Add each variable

## Workflow Behavior

The workflow triggers on:
- **Push to main** - Deploys to production
- **Pull requests to main** - Tests build without deployment (requires PR federated credential)
- **Manual trigger** - Via GitHub UI (Actions tab → Run workflow)

### What the workflow does:

1. ✅ Builds unified Docker image (React frontend + Flask backend)
2. ✅ Pushes image to Azure Container Registry with tags:
   - `<git-sha>` (immutable version)
   - `latest` (rolling tag)
3. ✅ Deploys container to App Service
4. ✅ Restarts App Service to pick up new image

## Verify Deployment

After workflow completes:

```bash
# Check deployment status
az webapp show --name <app-name> --resource-group <rg-name> --query "state" -o tsv

# View logs
az webapp log tail --name <app-name> --resource-group <rg-name>

# Get app URL
az webapp show --name <app-name> --resource-group <rg-name> --query "defaultHostName" -o tsv
```

Visit `https://<your-app-name>.azurewebsites.net` to see the deployed application.

## Troubleshooting

### Error: "Failed to get federated token"
- Verify federated credential `subject` matches your repo exactly
- Check that `permissions: id-token: write` is in workflow YAML

### Error: "Authorization failed for ACR"
- Ensure service principal has `AcrPush` role on ACR
- Verify ACR name variable is correct (without `.azurecr.io`)

### Error: "Resource not found"
- Double-check all variable names match exactly
- Run `az resource list` to verify resource names

### Deployment succeeds but app doesn't load
- Check App Service logs: `az webapp log tail --name <app-name> --resource-group <rg-name>`
- Verify container health: Look for "Container started successfully" in logs
- Check environment variables in Azure Portal → App Service → Configuration

## Security Notes

✅ **OIDC is more secure** than storing service principal credentials (no long-lived secrets in GitHub)  
✅ Federated credentials expire automatically after each workflow run  
✅ Permissions are scoped to specific resource groups
