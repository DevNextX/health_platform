# 统一容器部署说明（前端+后端+SQLite）

## 概述

本项目已调整为**统一容器部署**模式，将 React 前端、Flask 后端和 SQLite 数据库打包到一个 Docker 镜像中，简化 Azure App Service 部署流程。

## 架构变更

### 之前（分离部署）
- 前端：单独的静态文件托管或独立容器
- 后端：Python Flask API 容器
- 数据库：外部 MySQL 或容器内 SQLite

### 现在（统一容器）
- **单一容器**包含：
  - React 前端（编译后的静态文件）
  - Flask 后端（API + 静态文件服务）
  - SQLite 数据库（容器内 `/app/instance/health_platform.db`）
  - Gunicorn WSGI 服务器（生产级）

## 文件变更清单

### 1. 新增/修改的文件

| 文件 | 变更 |
|-----|------|
| [Dockerfile](../Dockerfile) | **新增**：多阶段构建，Stage 1 编译前端，Stage 2 运行后端 |
| [azure.yaml](../azure.yaml) | **修改**：`project` 改为 `./`，添加 `docker` 配置指向新 Dockerfile |
| [src/app.py](../src/app.py) | **修改**：添加前端静态文件服务路由（SPA 路由支持）|
| [.dockerignore](../.dockerignore) | **修改**：排除不必要文件，保留 `frontend/package*.json` 用于构建 |
| [infra/modules/appService.bicep](../infra/modules/appService.bicep) | **修改**：添加环境变量（`PORT=8000`、`CORS_ORIGINS` 等）|

### 2. Dockerfile 工作流程

```dockerfile
# Stage 1: Build React Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build  # 生成 /frontend/build

# Stage 2: Python Backend + Frontend
FROM python:3.11-slim AS runtime
WORKDIR /app
# 安装 Python 依赖
COPY requirements.txt ./
RUN pip install -r requirements.txt
# 复制后端代码
COPY src/ ./src/
COPY migrations/ ./migrations/
# 复制前端构建产物
COPY --from=frontend-builder /frontend/build ./frontend/build
# 运行迁移并启动 Gunicorn
CMD python run_migrations_manual.py && gunicorn "src.app:create_app()"
```

### 3. Flask 前端服务逻辑

在 `src/app.py` 中添加了以下路由：

```python
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    # 如果文件存在，直接返回（如 CSS/JS）
    if path and os.path.exists(os.path.join(frontend_build_dir, path)):
        return send_from_directory(frontend_build_dir, path)
    # 否则返回 index.html（支持 React Router）
    return send_from_directory(frontend_build_dir, "index.html")
```

**路由优先级**：
1. `/api/*` → 后端 API（优先级最高）
2. `/favicon.ico`、`/favicon.svg` → 204 空响应
3. `/*` → 前端静态文件或 `index.html`（SPA fallback）

## 部署流程

### 本地测试（可选）

```bash
# 构建镜像
docker build -t health-platform:local .

# 运行容器
docker run -p 8000:8000 \
  -e JWT_SECRET_KEY=test-secret \
  -e CORS_ORIGINS=http://localhost:8000 \
  health-platform:local

# 访问应用
open http://localhost:8000
```

### Azure 部署（azd）

#### 1. 初始化环境

```bash
azd init
# 选择 "Use code in the current directory"
# 输入环境名称（如 dev）
```

#### 2. 登录 Azure

```bash
az login
azd auth login
```

#### 3. 预览基础设施

```bash
azd provision --preview
```

**输出示例**：
- Resource Group: `rg-health-platform-dev`
- ACR: `crhealthplatformdev<suffix>.azurecr.io`
- Web App: `app-health-platform-dev-<suffix>.azurewebsites.net`
- Log Analytics + App Insights

#### 4. 部署应用

```bash
azd up
```

**执行步骤**：
1. `azd provision`：创建 Azure 资源（如果未执行过）
2. `azd package`：构建 Docker 镜像（使用远程构建或本地推送到 ACR）
3. `azd deploy`：更新 App Service 容器镜像并重启

#### 5. 验证部署

访问输出的 `SERVICE_API_ENDPOINT_URL`（如 `https://app-health-platform-dev-abc123.azurewebsites.net`），应同时看到：
- **前端**：登录页面（`/`）
- **后端 API**：健康检查（`/api/healthz` 返回 `{"status":"ok"}`）

### 关键环境变量（Bicep 自动设置）

| 变量 | 值 | 说明 |
|-----|-----|-----|
| `PORT` | `8000` | Gunicorn 监听端口（App Service 标准） |
| `FLASK_APP` | `src.app` | Flask 应用入口 |
| `SQLALCHEMY_DATABASE_URI` | `sqlite:///instance/health_platform.db` | 数据库路径（容器内） |
| `JWT_SECRET_KEY` | `uniqueString(...)` | 基于资源组 ID 生成的密钥 |
| `CORS_ORIGINS` | `https://<webAppName>.azurewebsites.net` | 允许前端调用后端 API |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | `(auto)` | 应用性能监控 |

## 数据持久化注意事项

⚠️ **重要**：SQLite 文件存储在**容器内**（`/app/instance/`），容器重启或重新部署时数据会丢失。

**生产环境建议**：
1. 切换到 **Azure Database for MySQL**（参考 `docs/plan/azure-infra-issue-89.md` 预留方案）
2. 或使用 **Azure Files** 挂载持久化 SQLite 文件（需修改 App Service `WEBSITES_ENABLE_APP_SERVICE_STORAGE=true`）

## 故障排查

### 1. 前端 404 / API 正常

**症状**：访问 `/` 返回 404，但 `/api/healthz` 正常。

**原因**：前端构建失败或未复制到容器。

**排查**：
```bash
# 查看容器日志
az webapp log tail --name <webAppName> --resource-group <rgName>

# 检查文件是否存在
az webapp ssh --name <webAppName> --resource-group <rgName>
ls -la /app/frontend/build
```

### 2. ACR 拉取失败（503/Unauthorized）

**原因**：Managed Identity 权限未生效或 `acrUserManagedIdentityID` 配置错误。

**验证**：
```bash
# 检查角色分配
az role assignment list --assignee <identity-principal-id> --scope <acr-resource-id>

# 确认 Web App 配置
az webapp config show --name <webAppName> --resource-group <rgName> \
  --query "siteConfig.acrUserManagedIdentityID"
# 应返回 clientId（形如 12345678-1234-...），不是 resourceId
```

### 3. CORS 错误

**症状**：浏览器控制台报 `Access-Control-Allow-Origin` 错误。

**解决**：
```bash
# 检查 CORS_ORIGINS 环境变量
az webapp config appsettings list --name <webAppName> --resource-group <rgName> \
  --query "[?name=='CORS_ORIGINS'].value" -o tsv

# 如需支持多个源（如开发环境 + 生产），手动更新：
az webapp config appsettings set --name <webAppName> --resource-group <rgName> \
  --settings CORS_ORIGINS="https://app-health-platform-dev-abc.azurewebsites.net,http://localhost:3000"
```

## 后续优化

- [ ] 集成 GitHub Actions CI/CD（自动构建镜像并推送到 ACR）
- [ ] 迁移到 Azure Database for MySQL（生产环境）
- [ ] 添加 Azure Front Door（CDN + WAF）
- [ ] 启用 App Service 诊断日志流到 Log Analytics

## 相关文档

- [Azure 基础设施规划](azure-infra-issue-89.md)
- [ACR 认证故障排查](../troubleshooting/acr-authentication-issue.md)
- [API 设计文档](../api/API_Design.md)
