# ACR Authentication Issue - acrUserManagedIdentityID Configuration Error

## 问题概述

**日期**: 2025年12月12日  
**严重程度**: 高（生产环境故障）  
**影响范围**: App Service 无法启动，返回 503 错误  
**解决时间**: 约 2-3 小时

## 问题症状

在执行 `azd provision` 更新基础设施后，Azure App Service (`appzavastorefrontapp-dev`) 出现以下症状：

1. **网站返回 503 Service Unavailable**
   - 主页面: `https://appzavastorefrontapp-dev.azurewebsites.net/` - 503
   - 健康检查端点: `/health` - 503

2. **容器日志显示持续的镜像拉取失败**
   ```
   ERROR - DockerApiException: Docker API responded with status code=NotFound, 
   response={"message":"manifest for crzavastorefrontappb3gitgkg7xekk.azurecr.io/zavastorefrontapp:fa22a5873bf125c645d8575e7345aa11463c4bf5 not found: manifest unknown: manifest tagged by \"fa22a5873bf125c645d8575e7345aa11463c4bf5\" is not found"}
   
   ERROR - DockerApiException: Docker API responded with status code=InternalServerError, 
   response={"message":"Head \"https://crzavastorefrontappb3gitgkg7xekk.azurecr.io/v2/zavastorefrontapp/manifests/fa22a5873bf125c645d8575e7345aa11463c4bf5\": unauthorized: {\"errors\":[{\"code\":\"UNAUTHORIZED\",\"message\":\"authentication required, visit https://aka.ms/acr/authorization for more information.\"}]}"}
   ```

3. **容器无法启动**
   ```
   Container pull image failed with reason: ImagePullFailure. Revert by terminate.
   Site container: appzavastorefrontapp-dev terminated during site startup.
   ```

## 根本原因

### Bicep 配置错误

在 `infra/modules/app-service.bicep` 中，`acrUserManagedIdentityID` 属性被错误地配置为使用 Managed Identity 的 **Resource ID**：

```bicep
// ❌ 错误配置
siteConfig: {
  acrUseManagedIdentityCreds: true
  acrUserManagedIdentityID: managedIdentity.id  // Resource ID - 错误！
}
```

### 为什么会出错？

1. **App Service 的 `acrUserManagedIdentityID` 需要 Client ID**
   - 该属性要求的是托管标识的 **Client ID** (GUID)
   - 而不是 **Resource ID** (完整的 Azure 资源路径)

2. **错误值导致的后果**
   - 当设置为 Resource ID 时，Azure 将其值设为 `null`
   - App Service 无法使用正确的托管标识进行 ACR 认证
   - 导致 `UNAUTHORIZED` 错误和镜像拉取失败

### 实际值对比

| 属性类型 | 示例值 | 是否正确 |
|---------|--------|---------|
| **Resource ID** | `/subscriptions/6ea984f1-ac84-4a4e-b9e1-dd4b5f2940a1/resourcegroups/copilot-workshop-rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/appzavastorefrontapp-dev-identity` | ❌ |
| **Client ID** | `5663a705-1118-4b9f-8e7b-a509f08163e2` | ✅ |

## 诊断过程

### 1. 初步检查

```bash
# 检查 App Service 状态
az webapp show --resource-group copilot-workshop-rg --name appzavastorefrontapp-dev
# 结果: state=Running, availabilityState=Normal（误导性，实际不可用）

# 检查容器日志
az rest --method post --url "https://management.azure.com/.../containerlogs?api-version=2023-01-01"
# 发现: ImagePullFailure 和 UNAUTHORIZED 错误
```

### 2. 权限验证

```bash
# 验证 RBAC 角色分配
az role assignment list --scope /subscriptions/.../Microsoft.ContainerRegistry/registries/...
# 结果: AcrPull 角色已正确分配给两个托管标识（系统分配和用户分配）
```

### 3. 镜像验证

```bash
# 验证镜像是否存在
az acr repository show-tags --name crzavastorefrontappb3gitgkg7xekk --repository zavastorefrontapp
# 结果: 镜像 fa22a5873bf125c645d8575e7345aa11463c4bf5 存在 ✅
```

### 4. 关键发现

```bash
# 检查 ACR 配置
az webapp config show --resource-group copilot-workshop-rg --name appzavastorefrontapp-dev \
  --query '{acrUseManagedIdentityCreds,acrUserManagedIdentityID}'

# 结果:
# {
#   "acrUseManagedIdentityCreds": true,
#   "acrUserManagedIdentityID": null  ⚠️ 这是问题所在！
# }
```

**acrUserManagedIdentityID 为 null** 导致 App Service 无法使用正确的托管标识。

## 解决方案

### 临时修复（生产环境）

使用 Azure REST API 直接设置正确的 Client ID：

```bash
# 1. 获取 Managed Identity 的 Client ID
az identity show --name appzavastorefrontapp-dev-identity \
  --resource-group copilot-workshop-rg \
  --query clientId -o tsv
# 输出: 5663a705-1118-4b9f-8e7b-a509f08163e2

# 2. 使用 REST API 更新配置
az rest --method patch \
  --url "https://management.azure.com/subscriptions/{subscription-id}/resourceGroups/copilot-workshop-rg/providers/Microsoft.Web/sites/appzavastorefrontapp-dev/config/web?api-version=2023-12-01" \
  --body '{"properties":{"acrUserManagedIdentityID":"5663a705-1118-4b9f-8e7b-a509f08163e2"}}'

# 3. 重启 App Service
az webapp restart --resource-group copilot-workshop-rg --name appzavastorefrontapp-dev
```

### 永久修复（Bicep 模板）

修改 `infra/modules/app-service.bicep`：

```bicep
resource appService 'Microsoft.Web/sites@2023-12-01' = {
  name: appServiceName
  location: location
  tags: tags
  kind: 'app,linux,container'
  identity: {
    type: 'SystemAssigned, UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'DOCKER|${containerRegistryUrl}/${dockerImageName}'
      acrUseManagedIdentityCreds: true
      // ✅ 修复: 使用 Client ID 而不是 Resource ID
      acrUserManagedIdentityID: managedIdentity.properties.clientId
      // ...
    }
  }
}
```

**关键变更**：
- 之前: `acrUserManagedIdentityID: managedIdentity.id` ❌
- 修复后: `acrUserManagedIdentityID: managedIdentity.properties.clientId` ✅

## 验证修复

```bash
# 1. 检查网站状态
curl -I https://appzavastorefrontapp-dev.azurewebsites.net/
# HTTP/1.1 200 OK ✅

# 2. 检查健康端点
curl https://appzavastorefrontapp-dev.azurewebsites.net/health
# Healthy ✅

# 3. 验证配置已更新
az webapp config show --resource-group copilot-workshop-rg \
  --name appzavastorefrontapp-dev \
  --query acrUserManagedIdentityID -o tsv
# 5663a705-1118-4b9f-8e7b-a509f08163e2 ✅
```

## 经验教训

### 1. **Bicep 属性文档需要仔细验证**
   - 不能仅凭注释或直觉来设置属性值
   - 应查阅官方 Azure 文档确认属性的确切要求
   - `acrUserManagedIdentityID` 需要 Client ID，而非 Resource ID

### 2. **容器日志是诊断的关键**
   - App Service 的状态可能显示 "Running"，但实际上容器无法启动
   - 必须查看容器日志 (`containerlogs`) 才能发现真正的错误
   - 命令: `az rest --method post --url ".../containerlogs?api-version=2023-01-01"`

### 3. **RBAC 权限配置正确不等于认证成功**
   - 即使 AcrPull 角色已分配，如果 `acrUserManagedIdentityID` 不正确，认证仍会失败
   - 需要验证完整的认证链：托管标识 → Client ID 配置 → RBAC 角色

### 4. **Bicep 部署可能产生意外的 null 值**
   - 当 Bicep 属性值类型不匹配时，Azure 可能将其设为 `null`
   - 需要在部署后验证关键配置是否正确应用

### 5. **系统分配托管标识作为备份**
   - 同时配置系统分配和用户分配托管标识的 AcrPull 权限是个好实践
   - 如果一个失败，另一个可能仍能工作

## 预防措施

### 1. **部署后验证清单**

创建自动化验证脚本 `verify-deployment.sh`：

```bash
#!/bin/bash
# 验证 App Service ACR 配置

RESOURCE_GROUP="copilot-workshop-rg"
APP_NAME="appzavastorefrontapp-dev"

echo "🔍 验证 ACR 配置..."

# 1. 检查 acrUserManagedIdentityID 不为 null
ACR_IDENTITY=$(az webapp config show -g $RESOURCE_GROUP -n $APP_NAME \
  --query acrUserManagedIdentityID -o tsv)

if [ -z "$ACR_IDENTITY" ] || [ "$ACR_IDENTITY" == "null" ]; then
  echo "❌ 错误: acrUserManagedIdentityID 为空或 null"
  exit 1
fi

echo "✅ acrUserManagedIdentityID: $ACR_IDENTITY"

# 2. 验证是否为有效的 GUID 格式
if [[ ! $ACR_IDENTITY =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
  echo "❌ 错误: acrUserManagedIdentityID 不是有效的 GUID"
  exit 1
fi

# 3. 检查健康端点
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$APP_NAME.azurewebsites.net/health)

if [ "$HTTP_STATUS" -eq 200 ]; then
  echo "✅ 健康检查通过 (HTTP $HTTP_STATUS)"
else
  echo "❌ 健康检查失败 (HTTP $HTTP_STATUS)"
  exit 1
fi

echo "✅ 所有验证通过！"
```

### 2. **CI/CD Pipeline 增强**

在 GitHub Actions workflow 中添加验证步骤：

```yaml
- name: Verify ACR Configuration
  run: |
    ACR_IDENTITY=$(az webapp config show \
      --resource-group ${{ env.RESOURCE_GROUP }} \
      --name ${{ env.APP_NAME }} \
      --query acrUserManagedIdentityID -o tsv)
    
    if [ -z "$ACR_IDENTITY" ] || [ "$ACR_IDENTITY" == "null" ]; then
      echo "::error::acrUserManagedIdentityID is null or empty"
      exit 1
    fi
    
    echo "::notice::ACR authentication configured with identity: $ACR_IDENTITY"
```

### 3. **文档更新**

在 `DEPLOY.md` 中添加故障排除章节，记录此问题和解决方法。

## 相关资源

- **Azure 文档**: [App Service - Use managed identity for ACR](https://learn.microsoft.com/en-us/azure/app-service/configure-custom-container#use-managed-identity-to-pull-image-from-azure-container-registry)
- **Bicep 属性参考**: `Microsoft.Web/sites/config@2023-12-01` - `acrUserManagedIdentityID`
- **修复的 Bicep 文件**: `infra/modules/app-service.bicep`

## 影响范围

- **受影响环境**: 所有使用此 Bicep 模板部署的环境
- **受影响时间**: 从 Bicep 错误引入到修复（约 2-3 小时生产故障）
- **用户影响**: 网站完全不可访问（503 错误）

## 状态

- ✅ **已修复** - 2025年12月12日
- ✅ **Bicep 模板已更新**
- ✅ **生产环境已恢复**
- 📋 **待办**: 将验证步骤集成到 CI/CD pipeline
