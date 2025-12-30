# Azure 开发环境基础设施方案（Issue #89）

**Issue**: https://github.com/DevNextX/health_platform/issues/89  
**目标环境**: dev  
**区域**: `westus3`（所有资源同区域，禁止跨区）  
**资源组**: 单资源组隔离（建议 `rg-health-platform-dev`）  
**IaC**: Bicep + Azure Developer CLI（AZD）  

## 1. 需求与边界

### 1.1 需求摘要（来自 Issue #89）
- 在 Azure 上搭建 Health Platform **开发环境**基础设施。
- 运行形态：**Linux App Service (Web App for Containers)**，通过 Docker 镜像部署。
- 镜像仓库：**Azure Container Registry (ACR)**。
- 容器拉取鉴权：**Azure RBAC + 托管身份（Managed Identity）**，不使用 ACR 密码（不启用 admin user）。
- 监控：集成 **Application Insights**（并配套 Log Analytics）。
- CI 构建/推送：使用 **GitHub Actions**（本地开发机不依赖 Docker 来推镜像）。
- 数据库：dev 使用容器内 **SQLite**；生产环境预留 **Azure Database for MySQL**（本 issue 不创建）。
- 未来扩展：预留 **Microsoft Foundry / GPT-4.1** 接入（本 issue 先不落资源，只预留参数与模块占位）。
- 安全：**不使用 Key Vault**；敏感配置采用 App Service 环境变量/配置文件注入。
- 本 issue 聚焦 **infra**；服务发布/完整 CI/CD 流程另开 issue。

### 1.2 非目标（明确不做）
- 不创建生产环境资源、不做多环境治理（仅 dev）。
- 不引入 VNet / 私网端点 / WAF 等复杂网络（MVP 简化）。
- 不落地 Foundry/OpenAI 资源本体（仅预留扩展点）。
- 不引入 Key Vault（后续再纳管）。

## 2. 目标架构（Dev）

### 2.1 资源清单（最小可用）
- Resource Group：`rg-health-platform-dev`（location: `westus3`）
- ACR：`cr<app><env><suffix>`（SKU: Basic；`adminUserEnabled=false`）
- App Service Plan（Linux）：建议 B1/S1 级别（按成本/配额调整）
- Web App（Linux, container）：从 ACR 拉取镜像
  - System Assigned Managed Identity（或 User Assigned，按实现偏好）
  - ACR `AcrPull` 角色分配
- Log Analytics Workspace：集中日志（App Service 诊断设置输出到此）
- Application Insights：应用性能/请求追踪（workspace-based，关联 Log Analytics）

### 2.2 身份与 RBAC
- Web App 托管身份（MI）
  - 对 ACR 赋予 `AcrPull`
- GitHub Actions（OIDC）建议：
  - 通过 Federated Credential 登录 Azure（避免长期密钥）
  - 对 ACR 赋予 `AcrPush`（或 Contributor 到 ACR scope）
  - 对资源组/应用的部署权限在后续 CI/CD issue 中细化

> 备注：App Service 通过托管身份拉 ACR 时，App Service 配置里 `acrUserManagedIdentityID` 需要 **Client ID** 而不是资源 ID（见仓库故障排查文档）。

## 3. 命名与参数化规范（Bicep/AZD）

### 3.1 命名建议
- `environment`: `dev`
- `location`: `westus3`
- `resourceGroupName`: `rg-health-platform-dev`
- `acrName`: `crhealthplatformdev<uniq>`（ACR 需全局唯一）
- `appServicePlanName`: `asp-health-platform-dev`
- `webAppName`: `app-health-platform-dev`（需全局唯一）
- `logAnalyticsName`: `log-health-platform-dev`
- `appInsightsName`: `appi-health-platform-dev`

### 3.2 参数
- `environment`, `location`, `namePrefix`, `sku`（ACR / ASP）
- `containerImage`（如 `health-platform-backend`）
- `containerTag`（默认用 git SHA，由部署流程写入）
- `enableFoundryPlaceholder`（仅占位，不创建资源）

## 4. IaC 目录结构（计划）

本仓库当前尚未生成 `infra/` 与 `azure.yaml`（issue 89 执行后应产生）。建议结构：

- `azure.yaml`
- `infra/main.bicep`
- `infra/modules/acr.bicep`
- `infra/modules/app-service.bicep`
- `infra/modules/log-analytics.bicep`
- `infra/modules/app-insights.bicep`
- `infra/params/dev.parameters.json`（可选）
- `next-step.md`（AZD 自动生成或手写）

模块职责：
- `acr.bicep`: ACR（禁用 admin user）、输出 `loginServer`、`id`
- `log-analytics.bicep`: Workspace
- `app-insights.bicep`: workspace-based App Insights
- `app-service.bicep`: ASP + Web App（容器配置、MI、诊断设置、App Settings）

## 5. App Service 容器配置要点

### 5.1 拉取镜像（Managed Identity + RBAC）
- Web App 启用 `acrUseManagedIdentityCreds=true`
- 配置 `acrUserManagedIdentityID` 为 **MI 的 clientId**
- ACR 侧对该 MI 赋予 `AcrPull`

### 5.2 应用配置（不使用 Key Vault）
- 通过 App Settings 写入：
  - `SQLALCHEMY_DATABASE_URI`（dev: sqlite）
  - `JWT_SECRET_KEY`（dev 可弱化，但仍需通过环境变量注入）
  - `CORS_ORIGINS` 等
  - `APPLICATIONINSIGHTS_CONNECTION_STRING`（或等价配置）

> 注意：此方案不涉及 secret 生命周期治理，后续若引入 Key Vault 需单独规划。

## 6. 监控与日志

- App Insights：请求、依赖、异常追踪
- Log Analytics：
  - 接收 App Service 诊断日志（HTTP、console、platform logs）
  - 作为 App Insights workspace 后端

运维基线：
- 统一在 `westus3`
- 默认保留期按 dev 最小化设置（如 30 天，后续按合规调整）

## 7. 部署工作流（AZD）

### 7.1 本地一次性部署（Infra）
- `azd init`：初始化工程（生成 `azure.yaml`、infra 结构）
- `azd provision`：创建/更新 Azure 资源（RG/ACR/ASP/WebApp/Logs/AI）

### 7.2 应用镜像构建与推送（GitHub Actions）
本 issue 只定义接口与前置要求（工作流细节在后续 CI/CD issue 完成）：
- Runner 执行 `docker buildx build` 构建镜像
- 推送到 ACR：`<acrLoginServer>/<image>:<gitSha>`
- Web App 更新镜像 tag（或通过 az/webapp config 变更），触发重启

推荐认证方式：GitHub OIDC + Azure Federated Credential。

## 8. 风险与常见坑（提前规避）

- **ACR 认证坑**：App Service `acrUserManagedIdentityID` 必须是 **clientId**，否则可能表现为 503 / 容器拉取未授权。
- **全局唯一命名**：ACR 与 Web App 名称需全局唯一，需在 Bicep 中加 suffix。
- **区域约束**：Foundry/模型可用性受区域限制，保持 `westus3` 并提前确认配额。
- **不使用 Key Vault**：短期简化，但长期存在 secret 治理风险（需列入后续 backlog）。

## 9. 验收清单（对齐 Issue #89）

- [ ] 所有资源创建在同一资源组 `rg-health-platform-dev`、同一区域 `westus3`
- [ ] ACR 创建成功，`adminUserEnabled=false`
- [ ] Web App 使用托管身份从 ACR 拉取镜像（RBAC `AcrPull`）
- [ ] Application Insights 可看到请求/异常（至少可接入）
- [ ] `azd provision` 可重复执行（幂等）
- [ ] 形成部署/维护文档（见下一节）

## 10. 文档产出（本计划对应）

- 本文档：`docs/plan/azure-infra-issue-89.md`
- 建议补充（实现时新增）：
  - `docs/ops/DEPLOYMENT-AZURE-DEV.md`：azd provision / 回滚 / 清理
  - `docs/troubleshooting/`：ACR 拉取、App Service 启动、日志排查 SOP
