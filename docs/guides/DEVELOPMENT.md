# 开发指南

本文档面向开发者，介绍如何搭建开发环境、运行测试和调试应用。

## 环境要求

- Python 3.10+
- Node.js 18+
- Git

## 开发环境搭建

> **重要**：后端和前端需在**两个独立终端**中运行，启动后请保持终端开启。

### 后端 (终端 1)

```cmd
cd c:\Zhuang\Source\health_platform
python -m venv .venv
.\.venv\Scripts\activate.bat
pip install -r requirements.txt
set PYTHONPATH=.
python -m flask --app src.app run --host=0.0.0.0 --port=5000
```

**其他 Shell**：
```bash
# PowerShell
$env:PYTHONPATH='.'; python -m flask --app src.app run --host=0.0.0.0 --port=5000

# Bash
export PYTHONPATH=. && python -m flask --app src.app run --host=0.0.0.0 --port=5000
```

### 前端 (终端 2)

```cmd
cd frontend
npm install
npm start
```

访问 http://localhost:3000

## 测试

### 单元测试 (Pytest)

```cmd
:: 全量运行
.\.venv\Scripts\python.exe -m pytest tests/ -v

:: 单个用例
.\.venv\Scripts\python.exe -m pytest tests/test_auth.py::TestAuthEndpoints::test_health_check -q

:: 关键字过滤
.\.venv\Scripts\python.exe -m pytest -k "login" -v

:: 首个失败即停
.\.venv\Scripts\python.exe -m pytest tests/ -x -v
```

### E2E 测试 (Playwright)

需先启动前后端：

```cmd
cd tests/e2e
npm install
npx playwright install --with-deps
npm run test
```

## 数据库

### 开发环境
SQLite 自动建表，无需配置。数据库文件位于 `src/instance/health_platform.db`。

### CLI 命令

```cmd
python -m flask db-info    # 查看数据库信息
python -m flask db-create  # 创建/补齐表结构
```

### 生产环境 (MySQL)

环境变量：
- `DATABASE_URL` - 数据库连接串
- `DB_AUTO_CREATE=1` - 强制自动建表
- `MYSQL_SSL=1` - 启用 TLS 连接

## 代码架构

```
src/
├── app.py              # Flask 应用入口
├── config.py           # 配置管理
├── models.py           # SQLAlchemy 模型
├── service/            # API 路由层（处理 HTTP）
│   ├── auth_service.py
│   ├── admin_service.py
│   ├── health_service.py
│   └── ...
└── manager/            # 业务逻辑层（处理数据库）
    ├── user_manager.py
    ├── health_manager.py
    └── ...
```

**分层原则**：
- **Service 层**：处理 HTTP 请求/响应、参数校验
- **Manager 层**：执行数据库查询/更新、业务逻辑
- 不要在 Service 层直接查询数据库

## 调试技巧

### 常见问题

| 问题 | 解决方案 |
|-----|---------|
| `ModuleNotFoundError` | 确认使用 `.venv` 解释器，重新安装依赖 |
| 前端 `ERR_CONNECTION_REFUSED` | 检查后端是否运行在 5000 端口 |
| JWT 过期 | 前端自动刷新，检查 `refresh_token` 是否有效 |

### 日志查看

- 后端日志：终端 1 输出
- 前端日志：浏览器 DevTools Console
- 数据库：SQLite 可用 DB Browser for SQLite 查看
