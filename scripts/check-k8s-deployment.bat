@echo off
REM Kubernetes 部署预检查脚本 (Windows)
REM 用于验证所有必需配置是否就绪

setlocal enabledelayedexpansion

echo.
echo [1;34m=========================================[0m
echo [1;36m Health Platform - K8s 部署预检查[0m
echo [1;34m=========================================[0m
echo.

set ERRORS=0
set WARNINGS=0

REM 1. 检查本地工具
echo [1;33m检查本地工具...[0m
where kubectl >nul 2>&1
if %errorlevel%==0 (
    echo [32m✓[0m kubectl 已安装
    kubectl version --client --short 2>nul
) else (
    echo [31m✗[0m kubectl 未安装
    set /a ERRORS+=1
)

where git >nul 2>&1
if %errorlevel%==0 (
    echo [32m✓[0m git 已安装
) else (
    echo [31m✗[0m git 未安装
    set /a ERRORS+=1
)

where gh >nul 2>&1
if %errorlevel%==0 (
    echo [32m✓[0m GitHub CLI 已安装
) else (
    echo [33m⚠[0m GitHub CLI 未安装 (可选)
    set /a WARNINGS+=1
)

echo.

REM 2. 检查 kubectl 连接
echo [1;33m检查 Kubernetes 集群连接...[0m
kubectl cluster-info >nul 2>&1
if %errorlevel%==0 (
    echo [32m✓[0m kubectl 可连接到集群
    for /f "tokens=*" %%i in ('kubectl config current-context 2^>nul') do set CURRENT_CONTEXT=%%i
    echo    当前 context: !CURRENT_CONTEXT!
) else (
    echo [31m✗[0m kubectl 无法连接到集群
    echo    请确保 kubeconfig 配置正确
    set /a ERRORS+=1
)

echo.

REM 3. 检查 GitHub 仓库
echo [1;33m检查 GitHub 仓库配置...[0m
if exist ".git" (
    for /f "tokens=*" %%i in ('git config --get remote.origin.url 2^>nul') do set REPO_URL=%%i
    echo [32m✓[0m Git 仓库: !REPO_URL!
) else (
    echo [31m✗[0m 不在 Git 仓库中
    set /a ERRORS+=1
)

echo.

REM 4. 检查环境配置文件
echo [1;33m检查环境配置文件...[0m
for %%E in (development staging production) do (
    set ENV_FILE=deploy\config\%%E.env
    if exist "!ENV_FILE!" (
        echo [32m✓[0m !ENV_FILE! 存在
        
        REM 检查 NAMESPACE
        findstr /B "NAMESPACE=" "!ENV_FILE!" >nul 2>&1
        if !errorlevel!==0 (
            for /f "tokens=2 delims==" %%N in ('findstr /B "NAMESPACE=" "!ENV_FILE!"') do (
                echo    └─ NAMESPACE: %%N
            )
        ) else (
            echo [31m   └─ 缺少 NAMESPACE 字段[0m
            set /a ERRORS+=1
        )
        
        REM 检查 REGISTRY_URL
        findstr /B "REGISTRY_URL=" "!ENV_FILE!" >nul 2>&1
        if !errorlevel!==0 (
            for /f "tokens=2 delims==" %%R in ('findstr /B "REGISTRY_URL=" "!ENV_FILE!"') do (
                echo    └─ REGISTRY_URL: %%R
            )
        ) else (
            echo [31m   └─ 缺少 REGISTRY_URL 字段[0m
            set /a ERRORS+=1
        )
    ) else (
        echo [31m✗[0m !ENV_FILE! 不存在
        set /a ERRORS+=1
    )
)

echo.

REM 5. 检查 Dockerfile
echo [1;33m检查 Dockerfile...[0m
if exist "Dockerfile.backend" (
    echo [32m✓[0m Dockerfile.backend 存在
) else (
    echo [31m✗[0m Dockerfile.backend 不存在
    set /a ERRORS+=1
)

if exist "Dockerfile.frontend.nonroot" (
    echo [32m✓[0m Dockerfile.frontend.nonroot 存在
) else (
    echo [31m✗[0m Dockerfile.frontend.nonroot 不存在
    set /a ERRORS+=1
)

echo.

REM 6. 检查 K8s 模板
echo [1;33m检查 Kubernetes 模板...[0m
if exist "deploy\k8s-template.yaml" (
    echo [32m✓[0m deploy\k8s-template.yaml 存在
) else (
    echo [31m✗[0m deploy\k8s-template.yaml 不存在
    set /a ERRORS+=1
)

echo.

REM 7. 检查 CI/CD workflow
echo [1;33m检查 GitHub Actions workflow...[0m
if exist ".github\workflows\ci.yml" (
    echo [32m✓[0m .github\workflows\ci.yml 存在
) else (
    echo [31m✗[0m .github\workflows\ci.yml 不存在
    set /a ERRORS+=1
)

echo.
echo [1;34m=========================================[0m
echo [1;36m检查结果汇总[0m
echo [1;34m=========================================[0m
echo.

if %ERRORS%==0 (
    echo [32m✓ 所有必需配置已就绪！[0m
) else (
    echo [31m✗ 发现 %ERRORS% 个错误[0m
)

if %WARNINGS% gtr 0 (
    echo [33m⚠ 发现 %WARNINGS% 个警告[0m
)

echo.

if %ERRORS%==0 (
    echo [1;32m下一步：[0m
    echo    1. 配置 GitHub Secrets:
    echo       - KUBE_CONFIG: kubectl 配置文件内容
    echo       - KUBE_CONTEXT: kubectl config current-context
    echo       - JWT_SECRET: openssl rand -hex 32
    echo       - DATABASE_URL: 数据库连接字符串 (可选)
    echo.
    echo    2. 进入 GitHub repo -^> Actions
    echo    3. 选择 'Build, Push and Deploy' workflow
    echo    4. 点击 'Run workflow' 并选择环境
    echo.
    echo [1;36m详细文档: docs\ops\KUBERNETES-DEPLOYMENT.md[0m
    exit /b 0
) else (
    echo [1;31m请先解决上述错误，然后重新运行此脚本[0m
    echo.
    echo [1;33m快速修复指南：[0m
    echo    - 配置 kubectl: 运行 'kubectl config view'
    echo    - 配置 GitHub Secrets: 参考 docs\ops\KUBERNETES-DEPLOYMENT.md
    echo    - 创建环境文件: 复制 deploy\config\development.env.example
    echo.
    echo [1;36m详细文档: docs\ops\KUBERNETES-DEPLOYMENT.md[0m
    exit /b 1
)
