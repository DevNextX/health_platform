#!/bin/bash
# Kubernetes 部署预检查脚本
# 用于验证所有必需配置是否就绪

set -e

echo "🔍 Health Platform - Kubernetes 部署预检查"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查计数器
ERRORS=0
WARNINGS=0

# 1. 检查本地工具
echo "📦 检查本地工具..."
if command -v kubectl &> /dev/null; then
    echo -e "${GREEN}✓${NC} kubectl 已安装: $(kubectl version --client --short 2>/dev/null || kubectl version --client)"
else
    echo -e "${RED}✗${NC} kubectl 未安装"
    ((ERRORS++))
fi

if command -v git &> /dev/null; then
    echo -e "${GREEN}✓${NC} git 已安装: $(git --version)"
else
    echo -e "${RED}✗${NC} git 未安装"
    ((ERRORS++))
fi

if command -v gh &> /dev/null; then
    echo -e "${GREEN}✓${NC} GitHub CLI 已安装: $(gh --version | head -1)"
else
    echo -e "${YELLOW}⚠${NC} GitHub CLI 未安装（可选，但推荐用于管理 Secrets）"
    ((WARNINGS++))
fi

echo ""

# 2. 检查 kubectl 连接
echo "🔌 检查 Kubernetes 集群连接..."
if kubectl cluster-info &> /dev/null; then
    echo -e "${GREEN}✓${NC} kubectl 可连接到集群"
    CURRENT_CONTEXT=$(kubectl config current-context)
    echo "   当前 context: ${CURRENT_CONTEXT}"
else
    echo -e "${RED}✗${NC} kubectl 无法连接到集群"
    echo "   请确保 kubeconfig 配置正确"
    ((ERRORS++))
fi

echo ""

# 3. 检查 GitHub 仓库配置
echo "🔧 检查 GitHub 仓库配置..."

if [ -d ".git" ]; then
    REPO_URL=$(git config --get remote.origin.url 2>/dev/null || echo "未配置")
    echo -e "${GREEN}✓${NC} Git 仓库: ${REPO_URL}"
    
    # 提取仓库所有者和名称
    if [[ "$REPO_URL" =~ github\.com[:/]([^/]+)/([^/]+)(\.git)?$ ]]; then
        REPO_OWNER="${BASH_REMATCH[1]}"
        REPO_NAME="${BASH_REMATCH[2]}"
        REPO_NAME="${REPO_NAME%.git}"
        echo "   仓库所有者: ${REPO_OWNER}"
        echo "   仓库名称: ${REPO_NAME}"
    else
        echo -e "${YELLOW}⚠${NC} 无法解析 GitHub 仓库信息"
        ((WARNINGS++))
    fi
else
    echo -e "${RED}✗${NC} 不在 Git 仓库中"
    ((ERRORS++))
fi

echo ""

# 4. 检查 GitHub Secrets（需要 gh CLI）
echo "🔐 检查 GitHub Secrets 配置..."
if command -v gh &> /dev/null && gh auth status &> /dev/null; then
    SECRETS_LIST=$(gh secret list 2>/dev/null || echo "")
    
    # 必需的 Secrets
    REQUIRED_SECRETS=("KUBE_CONFIG" "KUBE_CONTEXT" "JWT_SECRET")
    
    for SECRET in "${REQUIRED_SECRETS[@]}"; do
        if echo "$SECRETS_LIST" | grep -q "^${SECRET}"; then
            echo -e "${GREEN}✓${NC} ${SECRET} 已配置"
        else
            echo -e "${RED}✗${NC} ${SECRET} 未配置（必需）"
            ((ERRORS++))
        fi
    done
    
    # 可选的 Secrets
    if echo "$SECRETS_LIST" | grep -q "^DATABASE_URL"; then
        echo -e "${GREEN}✓${NC} DATABASE_URL 已配置（推荐用于生产）"
    else
        echo -e "${YELLOW}⚠${NC} DATABASE_URL 未配置（开发环境可使用默认 SQLite）"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}⚠${NC} 无法检查 Secrets（需要 gh CLI 并登录）"
    echo "   请手动验证以下 Secrets 是否已配置："
    echo "   - KUBE_CONFIG (必需)"
    echo "   - KUBE_CONTEXT (必需)"
    echo "   - JWT_SECRET (必需)"
    echo "   - DATABASE_URL (可选，生产推荐)"
    ((WARNINGS++))
fi

echo ""

# 5. 检查环境配置文件
echo "📋 检查环境配置文件..."
for ENV in development staging production; do
    ENV_FILE="deploy/config/${ENV}.env"
    if [ -f "$ENV_FILE" ]; then
        echo -e "${GREEN}✓${NC} ${ENV_FILE} 存在"
        
        # 检查关键字段
        if grep -q "^NAMESPACE=" "$ENV_FILE"; then
            NAMESPACE=$(grep "^NAMESPACE=" "$ENV_FILE" | cut -d'=' -f2)
            echo "   └─ NAMESPACE: ${NAMESPACE}"
        else
            echo -e "${RED}   └─ 缺少 NAMESPACE 字段${NC}"
            ((ERRORS++))
        fi
        
        if grep -q "^REGISTRY_URL=" "$ENV_FILE"; then
            REGISTRY_URL=$(grep "^REGISTRY_URL=" "$ENV_FILE" | cut -d'=' -f2)
            echo "   └─ REGISTRY_URL: ${REGISTRY_URL}"
        else
            echo -e "${RED}   └─ 缺少 REGISTRY_URL 字段${NC}"
            ((ERRORS++))
        fi
    else
        echo -e "${RED}✗${NC} ${ENV_FILE} 不存在"
        ((ERRORS++))
    fi
done

echo ""

# 6. 检查 Dockerfile
echo "🐳 检查 Dockerfile..."
if [ -f "Dockerfile.backend" ]; then
    echo -e "${GREEN}✓${NC} Dockerfile.backend 存在"
else
    echo -e "${RED}✗${NC} Dockerfile.backend 不存在"
    ((ERRORS++))
fi

if [ -f "Dockerfile.frontend.nonroot" ]; then
    echo -e "${GREEN}✓${NC} Dockerfile.frontend.nonroot 存在"
else
    echo -e "${RED}✗${NC} Dockerfile.frontend.nonroot 不存在"
    ((ERRORS++))
fi

echo ""

# 7. 检查 K8s 模板
echo "☸️  检查 Kubernetes 模板..."
if [ -f "deploy/k8s-template.yaml" ]; then
    echo -e "${GREEN}✓${NC} deploy/k8s-template.yaml 存在"
else
    echo -e "${RED}✗${NC} deploy/k8s-template.yaml 不存在"
    ((ERRORS++))
fi

echo ""

# 8. 检查 CI/CD workflow
echo "⚙️  检查 GitHub Actions workflow..."
if [ -f ".github/workflows/ci.yml" ]; then
    echo -e "${GREEN}✓${NC} .github/workflows/ci.yml 存在"
else
    echo -e "${RED}✗${NC} .github/workflows/ci.yml 不存在"
    ((ERRORS++))
fi

echo ""
echo "=========================================="
echo "📊 检查结果汇总"
echo "=========================================="

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ 所有必需配置已就绪！${NC}"
else
    echo -e "${RED}✗ 发现 ${ERRORS} 个错误${NC}"
fi

if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠ 发现 ${WARNINGS} 个警告${NC}"
fi

echo ""

if [ $ERRORS -eq 0 ]; then
    echo "🚀 下一步："
    echo "   1. 进入 GitHub repo → Actions"
    echo "   2. 选择 'Build, Push and Deploy' workflow"
    echo "   3. 点击 'Run workflow'"
    echo "   4. 选择环境并运行"
    echo ""
    echo "📖 详细文档: docs/ops/KUBERNETES-DEPLOYMENT.md"
    exit 0
else
    echo "❌ 请先解决上述错误，然后重新运行此脚本"
    echo ""
    echo "💡 快速修复指南："
    echo "   - 配置 kubectl: 运行 'kubectl config view' 检查配置"
    echo "   - 配置 GitHub Secrets: 运行 'gh secret set <SECRET_NAME>'"
    echo "   - 创建环境文件: 复制 deploy/config/development.env.example"
    echo ""
    echo "📖 详细文档: docs/ops/KUBERNETES-DEPLOYMENT.md"
    exit 1
fi
