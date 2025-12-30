# Kubernetes 部署指南 - Health Platform

## 概述

本项目采用 **Kubernetes (K8s)** 作为首选部署方案，支持多环境隔离（通过 namespace）、前后端分容器、自动 CI/CD 和灵活扩缩容。

## 架构设计

### 容器化策略
- **前端容器**：React SPA + Nginx (非 root 用户)
- **后端容器**：Flask API + Gunicorn
- **镜像仓库**：GitHub Container Registry (GHCR)
- **认证方式**：GitHub Actions 内置 `GITHUB_TOKEN`（自动）

### 环境隔离
| 环境 | Namespace | 触发分支 | 用途 |
|-----|-----------|---------|------|
| **development** | `health-platform-dev` | `dev*`, `MVP*` | 开发/测试 |
| **staging** | `health-platform-staging` | `staging`, Pull Request | 预发布/QA |
| **production** | `health-platform-prod` | `main` | 生产环境 |

### CI/CD 工作流 (ci.yml)

#### 自动触发条件
- **Push 到分支**：`main`, `staging`, `dev*`, `MVP*`
- **Pull Request** → `main`（部署到 staging 供 QA 验证）
- **手动触发**：Actions → Run workflow（可选环境/跳过构建）

#### 执行阶段
1. **check-changes**：智能检测文件变更，决定是否需要重建镜像
   - 仅 docs/CI 变更时跳过构建，直接部署配置更新
2. **build-and-push**：构建前后端镜像，推送到 GHCR
   - 后端：`ghcr.io/<your-org>/health-platform-backend:<tag>`
   - 前端：`ghcr.io/<your-org>/health-platform-frontend:<tag>`
3. **deploy**：应用 K8s manifests，更新部署

## 前置要求

### 1. Kubernetes 集群
- 已有可访问的 K8s 集群（本地 Minikube、云厂商 AKS/EKS/GKE 等）
- 集群 API 地址可从外部访问（GitHub Actions Runner 需要连接）

### 2. kubectl 配置
生成 kubeconfig 并获取 context 名称：

```bash
# 查看当前 context
kubectl config current-context

# 查看所有 contexts
kubectl config get-contexts

# 获取完整 kubeconfig（包含证书/密钥）
kubectl config view --minify --flatten > kubeconfig.yaml

# 重要：删除敏感字段后再复制到 GitHub Secrets
# 确保包含 clusters、users、contexts 完整信息
cat kubeconfig.yaml
```

### 3. GitHub Container Registry
- 项目需启用 GitHub Packages（默认启用）
- Actions 自动使用 `GITHUB_TOKEN` 推送镜像（无需额外配置）

## GitHub 配置清单

### 必需的 Secrets（Settings → Secrets and variables → Actions → Secrets）

| Secret 名称 | 说明 | 获取方式 |
|-----------|------|---------|
| **KUBE_CONFIG** | Kubernetes 集群配置文件（Base64 或原始 YAML） | `cat kubeconfig.yaml \| base64` 或直接粘贴 YAML |
| **KUBE_CONTEXT** | kubectl context 名称 | `kubectl config current-context` |
| **DATABASE_URL** | 数据库连接串（生产环境必需） | 示例：`mysql://user:pass@host:3306/dbname` 或 `sqlite:///instance/health_platform.db` |
| **JWT_SECRET** | JWT 签名密钥（生产环境必需） | 生成强随机字符串：`openssl rand -hex 32` |

### 可选的 Variables（Settings → Secrets and variables → Actions → Variables）

| Variable 名称 | 说明 | 默认值 |
|-------------|------|--------|
| **CORS_ORIGINS** | 允许的跨域来源（多个用逗号分隔） | 自动生成（基于 namespace） |
| **IMAGE_TAG** | 强制指定镜像 tag | 自动使用分支名（如 `main`, `dev-feature`） |

### GitHub Environments（可选但推荐）

为每个环境创建 Environment（Settings → Environments），可设置：
- **保护规则**：production 需人工审批
- **环境特定的 Secrets/Variables**：如不同环境的 `DATABASE_URL`

创建环境：
1. 进入 Settings → Environments → New environment
2. 创建 `development`、`staging`、`production`
3. 在每个环境下配置对应的 `DATABASE_URL`、`JWT_SECRET`

## 快速开始

### 步骤 1：配置 GitHub Secrets

```bash
# 1. 获取 kubeconfig（假设使用 AKS）
az aks get-credentials --resource-group <rg-name> --name <cluster-name> --file kubeconfig.yaml

# 2. 获取 context 名称
KUBE_CONTEXT=$(kubectl config current-context)
echo "Context: $KUBE_CONTEXT"

# 3. Base64 编码（可选，也可直接粘贴原始 YAML）
cat kubeconfig.yaml | base64 -w 0 > kubeconfig.base64.txt

# 4. 在 GitHub repo 中添加 Secrets：
# - KUBE_CONFIG: 粘贴 kubeconfig.yaml 或 kubeconfig.base64.txt 的内容
# - KUBE_CONTEXT: 粘贴上面的 context 名称
# - DATABASE_URL: 根据实际情况填写
# - JWT_SECRET: openssl rand -hex 32
```

### 步骤 2：验证环境配置文件

检查 `deploy/config/` 下的 `.env` 文件，确保参数正确：

```bash
# 查看开发环境配置
cat deploy/config/development.env

# 关键字段：
# - NAMESPACE: 确保不与其他项目冲突
# - REGISTRY_URL: 确保匹配你的 GitHub 组织名
# - BACKEND_REPLICAS/FRONTEND_REPLICAS: 根据集群资源调整
# - 资源限制: 根据实际需求调整 CPU/内存
```

### 步骤 3：首次手动触发部署

1. 进入 GitHub repo → **Actions** tab
2. 选择 **Build, Push and Deploy** workflow
3. 点击 **Run workflow**
4. 选择参数：
   - **Branch**: 选择要部署的分支（如 `main`）
   - **Deployment Environment**: 选择 `development`
   - **Skip build**: 保持 `false`（首次需要构建镜像）
   - **Deploy to Kubernetes**: 保持 `true`
5. 点击 **Run workflow**

### 步骤 4：监控部署进度

在 Actions 页面查看实时日志：
- ✅ **check-changes**: 分析变更
- ✅ **build-and-push**: 构建并推送镜像到 GHCR
- ✅ **deploy**: 部署到 K8s 集群

部署成功后，可在本地验证：

```bash
# 切换到部署的 namespace
kubectl config set-context --current --namespace=health-platform-dev

# 查看 Pods 和 Services
kubectl get pods,svc

# 查看详细信息
kubectl describe deployment backend
kubectl describe deployment frontend

# 查看日志
kubectl logs -l app=backend --tail=100
kubectl logs -l app=frontend --tail=100
```

### 步骤 5：访问应用

```bash
# 获取 Service 外部 IP（如果 SERVICE_TYPE=LoadBalancer）
kubectl get svc frontend-svc

# 如果是 LoadBalancer，访问 http://<EXTERNAL-IP>
# 如果是 NodePort，访问 http://<NODE-IP>:<NODE-PORT>
# 如果是 ClusterIP（本地测试），使用端口转发：
kubectl port-forward svc/frontend-svc 3000:80
# 然后访问 http://localhost:3000
```

## 常见场景

### 场景 1：只更新代码（自动构建）

```bash
# 1. 修改代码（如 src/ 或 frontend/）
git add .
git commit -m "feat: add new feature"
git push origin dev-feature

# 2. GitHub Actions 自动触发：
# - 检测到 src/ 变更
# - 自动构建新镜像
# - 推送到 GHCR
# - 部署到 K8s
```

### 场景 2：只更新配置（跳过构建）

```bash
# 1. 修改 deploy/config/development.env（如调整 BACKEND_REPLICAS）
git add deploy/config/development.env
git commit -m "chore: increase backend replicas"
git push origin dev-feature

# 2. GitHub Actions 自动触发：
# - 检测到只有 deploy/ 变更
# - 跳过镜像构建
# - 直接应用新配置到 K8s
```

### 场景 3：手动部署已有镜像

适用于回滚或重新部署：

1. GitHub repo → Actions → Run workflow
2. 设置 **Skip build**: `true`
3. 设置 **IMAGE_TAG** Variable 为目标版本（如 `sha-abc123`）
4. 运行 workflow

### 场景 4：PR 测试（自动部署到 staging）

```bash
# 1. 创建 PR 到 main 分支
gh pr create --base main --head dev-feature

# 2. GitHub Actions 自动触发：
# - 构建镜像
# - 部署到 staging namespace
# - QA 团队在 staging 环境验证

# 3. 验证通过后，合并 PR → 自动部署到 production
gh pr merge <pr-number>
```

## 故障排查

### 问题 1：ImagePullBackOff / ErrImagePull

**症状**：Pod 状态显示 `ImagePullBackOff`

**原因**：K8s 无法从 GHCR 拉取镜像

**排查步骤**：

```bash
# 1. 检查镜像是否存在
kubectl describe pod <pod-name> -n health-platform-dev

# 2. 检查 imagePullSecret 是否创建
kubectl get secret ghcr-secret -n health-platform-dev

# 3. 验证 Secret 内容
kubectl get secret ghcr-secret -n health-platform-dev -o jsonpath='{.data.\.dockerconfigjson}' | base64 -d | jq

# 4. 手动测试拉取
docker login ghcr.io -u <your-username> -p <GITHUB_TOKEN>
docker pull ghcr.io/<your-org>/health-platform-backend:main
```

**解决方案**：
- 确保镜像已推送到 GHCR（Actions → Packages 查看）
- 确保仓库可见性为 Public，或配置正确的 imagePullSecret
- 检查 `REGISTRY_URL` 在 `.env` 中是否正确（如 `ghcr.io/devnextx`）

### 问题 2：CrashLoopBackOff

**症状**：Pod 反复重启

**原因**：容器启动失败（应用错误、配置问题等）

**排查步骤**：

```bash
# 查看容器日志
kubectl logs <pod-name> -n health-platform-dev --tail=200

# 查看 Pod 事件
kubectl describe pod <pod-name> -n health-platform-dev

# 进入容器调试（如果容器未完全崩溃）
kubectl exec -it <pod-name> -n health-platform-dev -- sh

# 检查环境变量是否正确
kubectl exec <pod-name> -n health-platform-dev -- env | grep -E 'DATABASE|JWT|CORS'
```

**常见原因**：
- `DATABASE_URL` 配置错误（连接串格式、密码错误）
- `JWT_SECRET` 未设置
- 缺少必要的依赖包
- 健康检查端点 `/api/healthz` 或 `/nginx-health` 不可用

### 问题 3：Service 无法访问

**症状**：`kubectl get svc` 显示 Service，但无法访问

**排查步骤**：

```bash
# 1. 检查 Service 类型和端口
kubectl get svc -n health-platform-dev

# 2. 检查 Endpoints（确保 Pod 已就绪）
kubectl get endpoints -n health-platform-dev

# 3. 测试 Service 内部连通性
kubectl run -it --rm debug --image=busybox --restart=Never -- sh
# 在容器内：
wget -qO- http://backend-svc.health-platform-dev.svc.cluster.local:5000/api/healthz

# 4. 如果是 LoadBalancer，检查云厂商负载均衡器配置
# Azure: az network lb list
# AWS: aws elb describe-load-balancers
# GCP: gcloud compute forwarding-rules list
```

### 问题 4：部署超时 (rollout timeout)

**症状**：GitHub Actions 日志显示 `waiting for deployment rollout to finish: 0 of 1 updated replicas are available`

**原因**：Pod 启动时间过长，超过 5 分钟超时限制

**解决方案**：

```bash
# 1. 检查资源限制是否过低
kubectl describe deployment backend -n health-platform-dev

# 2. 调整 deployment.env 中的资源配置
# BACKEND_MEMORY_LIMIT=1Gi
# BACKEND_CPU_LIMIT=1000m

# 3. 检查是否卡在镜像拉取
kubectl get events -n health-platform-dev --sort-by='.lastTimestamp' | tail -20

# 4. 临时增加超时时间（修改 ci.yml）
# kubectl rollout status deployment/backend -n ${NAMESPACE} --timeout=600s
```

## 高级配置

### 1. 自定义镜像 Tag 策略

在 GitHub Variables 中设置 `IMAGE_TAG`：

```bash
# 使用特定版本
IMAGE_TAG=v1.2.3

# 使用 Git SHA（推荐，便于追溯）
IMAGE_TAG=sha-$(git rev-parse --short HEAD)

# 使用分支名（默认行为）
IMAGE_TAG=main
```

### 2. 启用 Ingress（外部访问）

修改 `deploy/k8s-template.yaml`，添加 Ingress 资源：

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: health-platform-ingress
  namespace: ${NAMESPACE}
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - health-platform.example.com
    secretName: health-platform-tls
  rules:
  - host: health-platform.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-svc
            port:
              number: 80
```

### 3. 配置持久化存储（PVC）

如需持久化 SQLite 数据（不推荐生产）：

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: backend-data
  namespace: ${NAMESPACE}
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
# 在 backend Deployment 中挂载
volumes:
- name: data
  persistentVolumeClaim:
    claimName: backend-data
volumeMounts:
- name: data
  mountPath: /app/instance
```

**生产建议**：使用外部 MySQL/PostgreSQL，而非容器内 SQLite

### 4. 配置 Horizontal Pod Autoscaler (HPA)

自动根据 CPU/内存负载扩缩容：

```bash
# 为后端配置 HPA（CPU > 70% 时扩容）
kubectl autoscale deployment backend -n health-platform-dev \
  --min=2 --max=10 --cpu-percent=70

# 为前端配置 HPA
kubectl autoscale deployment frontend -n health-platform-dev \
  --min=2 --max=5 --cpu-percent=80

# 查看 HPA 状态
kubectl get hpa -n health-platform-dev
```

## 环境变量优先级

CI/CD 中的环境变量采用三层覆盖策略（由低到高）：

| 优先级 | 来源 | 适用场景 | 示例 |
|-------|------|---------|------|
| **3 (低)** | `deploy/config/${ENVIRONMENT}.env` | 基础配置、非敏感参数 | `BACKEND_REPLICAS=1` |
| **2 (中)** | GitHub Variables | 环境特定的非敏感配置 | `CORS_ORIGINS=https://example.com` |
| **1 (高)** | GitHub Secrets (Environment-specific) | 敏感信息、凭证 | `DATABASE_URL=mysql://...` |

**最佳实践**：
- 敏感信息（密码、密钥）→ GitHub Secrets
- 环境特定配置（域名、副本数）→ GitHub Variables 或 Environment-specific Secrets
- 通用配置（镜像仓库、资源限制）→ `.env` 文件

## 监控和日志

### 查看实时日志

```bash
# 后端日志（流式输出）
kubectl logs -f deployment/backend -n health-platform-dev

# 前端日志
kubectl logs -f deployment/frontend -n health-platform-dev

# 查看所有 Pods 日志
kubectl logs -l app=backend -n health-platform-dev --tail=100
```

### 集成日志聚合（可选）

推荐使用 ELK/EFK Stack 或云厂商日志服务：
- **Azure**: Azure Monitor for containers
- **AWS**: CloudWatch Logs
- **GCP**: Cloud Logging

### 监控指标

```bash
# 查看资源使用情况
kubectl top nodes
kubectl top pods -n health-platform-dev

# 查看 Deployment 状态
kubectl get deployments -n health-platform-dev -o wide
```

## 回滚策略

### 方法 1：K8s 原生回滚

```bash
# 查看部署历史
kubectl rollout history deployment/backend -n health-platform-dev

# 回滚到上一个版本
kubectl rollout undo deployment/backend -n health-platform-dev

# 回滚到特定版本
kubectl rollout undo deployment/backend -n health-platform-dev --to-revision=3
```

### 方法 2：重新部署旧镜像

1. 在 GitHub Actions 手动触发 workflow
2. 设置 `IMAGE_TAG` 为旧版本（如 `sha-abc123`）
3. 勾选 `Skip build` = `true`
4. 运行部署

### 方法 3：Git 回滚 + 重新部署

```bash
# 回滚代码到上一个 commit
git revert <commit-sha>
git push origin main

# GitHub Actions 自动触发，重新构建并部署
```

## 清理资源

### 删除特定环境

```bash
# 删除整个 namespace（包括所有资源）
kubectl delete namespace health-platform-dev

# 仅删除部署（保留 namespace）
kubectl delete deployment backend frontend -n health-platform-dev
kubectl delete svc backend-svc frontend-svc -n health-platform-dev
```

### 删除旧镜像

```bash
# 在 GitHub repo → Packages 中手动删除旧版本
# 或使用 GitHub CLI
gh api -X DELETE /user/packages/container/health-platform-backend/versions/<version-id>
```

## 与 App Service 部署对比

| 维度 | Kubernetes | App Service |
|-----|-----------|------------|
| **前后端** | 分容器（灵活） | 合一容器（简单） |
| **环境隔离** | Namespace（灵活） | 资源组/订阅 |
| **扩缩容** | HPA/手动 | 手动/自动 |
| **成本** | 按节点计费 | 按实例计费 |
| **运维复杂度** | 高（需 K8s 知识） | 低（托管服务） |
| **适用场景** | 多环境、高并发、团队协作 | 极简单体、快速 PoC |

## 相关文档

- [开发环境搭建](../docs/DEVELOPMENT.md)
- [Docker 镜像构建](../Dockerfile.backend)（后端）
- [Docker 镜像构建](../Dockerfile.frontend.nonroot)（前端）
- [K8s Manifest 模板](../deploy/k8s-template.yaml)
- [环境配置文件](../deploy/config/)

## 常见问题 FAQ

**Q: 为什么选择 K8s 而不是 App Service？**  
A: K8s 支持多环境 namespace 隔离、前后端独立扩缩容、无缝集成 CI/CD，适合团队协作和长期演进。

**Q: 镜像构建很慢，如何优化？**  
A: 利用 Docker 层缓存、缩小镜像体积（多阶段构建）、使用更快的 Runner（self-hosted）。

**Q: 如何支持多租户（不同客户）？**  
A: 为每个租户创建独立 namespace，或使用相同 namespace 但不同 Service 前缀。

**Q: 生产环境应该用 SQLite 吗？**  
A: 不推荐。SQLite 不适合多副本/高并发场景，生产应使用 MySQL/PostgreSQL。

**Q: 如何启用 HTTPS？**  
A: 使用 Ingress + cert-manager 自动签发 Let's Encrypt 证书（参考"高级配置"章节）。

---

**贡献与反馈**：如有疑问或建议，请在 GitHub Issues 中提出。
