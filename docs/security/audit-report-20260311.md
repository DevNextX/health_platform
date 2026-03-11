# 安全审计报告：健康记录平台全量审计

**日期**：2026-03-11
**审计员**：Security_Tester Agent（GitHub Copilot - Claude Sonnet 4.6）
**范围**：`src/`（Flask 后端）、`frontend/src/`（React 前端）、配置文件、容器化配置
**分支**：main
**分析类型**：静态代码审计（SAST）

---

## 执行摘要

| 严重程度 | 数量 |
|----------|------|
| 🔴 严重（Critical） | 1 |
| 🟠 高危（High） | 5 |
| 🟡 中危（Medium） | 7 |
| 🔵 低危（Low） | 3 |
| ⚪ 信息（Informational） | 2 |
| **合计** | **18** |

**综合风险等级**：🟠 **高危（High）**

系统整体安全设计具备一定水准（bcrypt 哈希、JWT token_version 吊销、`secure_filename()` 净化、MIME 二重验证、SQLAlchemy ORM 等均已正确实施），但存在多项直接可被利用的 High/Critical 级别漏洞，包括弱默认 JWT 密钥、内部异常信息直接暴露给客户端、Admin 临时密码明文传输，以及 JWT 存储于 localStorage 带来的 XSS 横向风险，必须在下次发布前修复。

---

## 已证实安全优势（正面基线）

| 控制点 | 位置 | 状态 |
|--------|------|------|
| bcrypt 密码哈希 | `src/security.py` | ✅ 已实施 |
| JWT token_version 吊销机制 | `src/service/auth_service.py` | ✅ 已实施 |
| `secrets` 模块生成临时密码 | `src/security.py` | ✅ 已实施 |
| 密码重置防用户枚举 | `src/manager/password_reset_request_manager.py` | ✅ 已实施 |
| `secure_filename()` 附件名净化 | `src/manager/medical_history_attachment_manager.py` | ✅ 已实施 |
| 扩展名 + MIME 二重文件校验 | `src/service/medical_history_service.py` | ✅ 已实施 |
| SQLAlchemy ORM（无原始 SQL 注入） | `src/manager/` 全局 | ✅ 已实施 |
| 批量导入 5 MB + 1000 行硬限制 | `src/service/health_service.py` | ✅ 已实施 |
| Docker 非 root 用户运行 | `Dockerfile` | ✅ 已实施 |
| 前端无 `dangerouslySetInnerHTML` | `frontend/src/` | ✅ 确认 |
| refresh 失败自动登出 | `frontend/src/services/api.js` | ✅ 已实施 |
| `must_change_password` 强制改密流程 | `src/app.py`, `src/service/auth_service.py` | ✅ 已实施 |

---

## 按 STRIDE 分类的漏洞详情

---

### S — Spoofing（身份伪造）

---

#### [S-01] JWT 密钥与会话密钥使用弱硬编码默认值

| 字段 | 详情 |
|------|------|
| **严重程度** | 🔴 严重（Critical） |
| **置信度** | ✅ 已确认 |
| **OWASP** | A07:2021 – 身份认证与认证失败 |
| **STRIDE** | Spoofing |
| **文件** | `src/config.py` |
| **行号** | L26、L35 |

**描述**：
`JWT_SECRET_KEY` 和 `SECRET_KEY` 均以 `"dev-secret-change-me"` 作为默认值。若生产环境未通过环境变量显式覆盖，任何知道此默认值的攻击者均可伪造任意用户身份的 JWT，实现完全账户接管。

**证据**：
```python
# src/config.py L26
SECRET_KEY = os.getenv("SECRET_KEY", os.getenv("JWT_SECRET", "dev-secret-change-me"))

# src/config.py L35
JWT_SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-me")
```

**此外**，`SECRET_KEY` 回退到 `JWT_SECRET`，且两者共享同一个弱默认值，无任何密钥分离：
```python
# L26 回退路径：SECRET_KEY -> JWT_SECRET -> "dev-secret-change-me"
# L35 路径：JWT_SECRET_KEY -> JWT_SECRET -> "dev-secret-change-me"
# 两者本质上是同一个密钥，丧失了密钥隔离的意义
```

**修复建议**：
- 移除所有魔法字符串默认值，改为 `os.getenv("JWT_SECRET_KEY")` 并在 `None` 时启动即报错（fail-fast）。
- `SECRET_KEY` 与 `JWT_SECRET_KEY` 使用独立的环境变量，禁止相互回退。
- 生产环境使用 `secrets.token_hex(32)` 生成至少 256 位的强密钥并写入 CI/CD Secrets。

---

#### [S-02] docker-compose.yml 硬编码弱 MySQL 密码与弱 JWT 默认密钥

| 字段 | 详情 |
|------|------|
| **严重程度** | 🟠 高危（High） |
| **置信度** | ✅ 已确认 |
| **OWASP** | A05:2021 – 安全误配置 |
| **STRIDE** | Spoofing |
| **文件** | `docker-compose.yml` |
| **行号** | L10（DATABASE_URL）、L13（JWT_SECRET） |

**描述**：
`docker-compose.yml` 中硬编码了 MySQL 凭据 `user:password` 和 JWT 默认值 `dev-change-me`。在 docker-compose 开发环境直接可被利用，若误推送到生产亦构成重大风险。

**证据**：
```yaml
# docker-compose.yml
DATABASE_URL: mysql+pymysql://user:password@mysql:3306/healthdb
JWT_SECRET: ${JWT_SECRET:-dev-change-me}
```

**修复建议**：
- 移除 `docker-compose.yml` 中的明文密码，改用 `${MYSQL_PASSWORD}` 并从 `.env` 注入。
- 删除 `JWT_SECRET` 的 `:-dev-change-me` 回退，改为无默认值（`${JWT_SECRET:?JWT_SECRET must be set}`）。
- 提供 `.env.example` 文件（参见 SEC-016）。

---

#### [S-06] SUPER_ADMIN 弱默认密码

| 字段 | 详情 |
|------|------|
| **严重程度** | 🟠 高危（High） |
| **置信度** | ✅ 已确认 |
| **OWASP** | A07:2021 – 身份认证与认证失败 |
| **STRIDE** | Spoofing |
| **文件** | `src/app.py` |
| **行号** | L162–L166 |

**描述**：
超级管理员在未配置 `SUPER_ADMIN_PASSWORD` 环境变量时使用 `"ChangeMe123"` 作为默认密码。虽后续有 `must_change_password = True` 保护，但该密码为可猜测字符串，攻击者若在强制改密前登录可获得 SUPER_ADMIN 权限。

**证据**：
```python
# src/app.py L162-166
sa_password = os.getenv("SUPER_ADMIN_PASSWORD", "ChangeMe123")
# ...
sa.must_change_password = True
```

**修复建议**：
- 生产部署强制要求 `SUPER_ADMIN_PASSWORD` 非空（启动时校验）。
- 首次初始化时改用随机生成密码并输出到安全日志，而非硬编码默认值。

---

#### [S-08] 速率限制基于 IP，可被 X-Forwarded-For 头绕过

| 字段 | 详情 |
|------|------|
| **严重程度** | 🟡 中危（Medium） |
| **置信度** | ✅ 已确认 |
| **OWASP** | A04:2021 – 不安全设计 |
| **STRIDE** | Spoofing / Denial of Service |
| **文件** | `src/extensions.py` |
| **行号** | L12 |

**描述**：
Flask-Limiter 使用 `get_remote_address`（即 `request.remote_addr`）作为限速 key。在反向代理或 Kubernetes Ingress 后运行时，`remote_addr` 可能始终为代理 IP，攻击者可通过伪造 `X-Forwarded-For` 头绕过限速。

**证据**：
```python
# src/extensions.py L12
Limiter(key_func=get_remote_address)
```

**修复建议**：
- 在 Kubernetes/代理环境中，改用 `request.headers.get('X-Real-IP')` 并僅信任已知代理源。
- 或配合 Flask-Limiter 的 `ProxiedRemoteAddr` 并严格设置 `TRUSTED_PROXIES`。

---

#### [S-13] SECRET_KEY 与 JWT_SECRET_KEY 共享同一弱默认值

| 字段 | 详情 |
|------|------|
| **严重程度** | 🟡 中危（Medium） |
| **置信度** | ✅ 已确认 |
| **OWASP** | A02:2021 – 密码学失败 |
| **STRIDE** | Spoofing |
| **文件** | `src/config.py` |
| **行号** | L26 |

**描述**：
`SECRET_KEY` 的回退路径为 `JWT_SECRET`，导致 Flask session 密钥与 JWT 签名密钥共享同一个环境变量（且共享同一弱默认值）。密钥分离原则遭到破坏。

**证据**：
```python
# src/config.py L26
SECRET_KEY = os.getenv("SECRET_KEY", os.getenv("JWT_SECRET", "dev-secret-change-me"))
```

**修复建议**：
- 将 `SECRET_KEY`（Flask session）与 `JWT_SECRET_KEY`（JWT 签名）配置为完全独立的环境变量，无相互回退。

---

#### [S-14] 密码强度要求仅需字母 + 数字，无大写/特殊字符要求

| 字段 | 详情 |
|------|------|
| **严重程度** | 🔵 低危（Low） |
| **置信度** | ✅ 已确认 |
| **OWASP** | A07:2021 – 身份认证与认证失败 |
| **STRIDE** | Spoofing |
| **文件** | `src/security.py` |
| **行号** | L36–L41 |

**描述**：
`validate_password_strength` 仅要求密码长度 ≥ 8 且同时包含字母与数字，不要求大写字母、小写字母、特殊字符，密码熵较低。

**证据**：
```python
# src/security.py L36-41
def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[a-zA-Z]', password) or not re.search(r'\d', password):
        return False, "Password must contain both letters and numbers"
    return True, ""
```

**修复建议**：
- 至少要求长度 ≥ 12，并包含大写、小写、数字各一。
- 可选：接入 NIST 推荐的密码黑名单（如 HaveIBeenPwned API）。

---

#### [S-15] 注册接口 "Email already exists" 409 暴露邮箱是否已注册

| 字段 | 详情 |
|------|------|
| **严重程度** | 🔵 低危（Low） |
| **置信度** | ✅ 已确认 |
| **OWASP** | A01:2021 – 访问控制失效 |
| **STRIDE** | Spoofing / Information Disclosure |
| **文件** | `src/service/auth_service.py` |
| **行号** | L97 |

**描述**：
注册接口返回 `"Email already exists"` 允许攻击者枚举哪些邮箱地址已在系统中注册，可辅助撞库攻击。

**证据**：
```python
# src/service/auth_service.py L97
return jsonify(error("409", "Email already exists"))
```

**修复建议**：
- 改为通用提示 `"Registration failed"` 或 `"Invalid credentials or email already in use"`。

---

### T — Tampering（数据 / 代码篡改）

---

#### [T-07] 缺少关键安全 HTTP 响应头（CSP、X-Frame-Options 等）

| 字段 | 详情 |
|------|------|
| **严重程度** | 🟡 中危（Medium） |
| **置信度** | ✅ 已确认 |
| **OWASP** | A05:2021 – 安全误配置 |
| **STRIDE** | Tampering |
| **文件** | `src/app.py`（全局未找到） |
| **行号** | 全局缺失 |

**描述**：
Flask 应用未设置以下 HTTP 安全响应头，存在 Clickjacking、MIME 类型嗅探和 XSS 放大风险：
- `Content-Security-Policy`（CSP）
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy`

**修复建议**：
- 集成 `Flask-Talisman`（`pip install flask-talisman`），可一行代码注入标准安全头。
- CSP 最低配置：`default-src 'self'; script-src 'self'; object-src 'none'`。

---

#### [T-10] MySQL SSL 启用但无 CA 证书验证（MITM 风险）

| 字段 | 详情 |
|------|------|
| **严重程度** | 🟡 中危（Medium） |
| **置信度** | ✅ 已确认 |
| **OWASP** | A02:2021 – 密码学失败 |
| **STRIDE** | Tampering / Information Disclosure |
| **文件** | `src/app.py` |
| **行号** | L74–L84 |

**描述**：
当 `MYSQL_SSL=1` 但未提供 `MYSQL_SSL_CA` 时，`connect_args` 设置为空字典 `{"ssl": {}}`，即启用了 SSL 加密传输，但未验证服务器证书。在公共或共享网络环境下存在中间人攻击（MITM）风险。

**证据**：
```python
# src/app.py L78-80（简化示意）
if os.getenv("MYSQL_SSL"):
    ca = os.getenv("MYSQL_SSL_CA")
    ssl_args = {"ssl": {"ca": ca} if ca else {}}  # 无 CA 时空字典
```

**修复建议**：
- 当 `MYSQL_SSL=1` 且 `MYSQL_SSL_CA` 未配置时，打印警告日志并建议配置 CA 证书。
- 生产环境强制提供 `MYSQL_SSL_CA`，或设置 `ssl_verify_cert=True`。

---

#### [T-11] 医疗附件存储路径无 `.resolve()` 规范化（潜在路径遍历）

| 字段 | 详情 |
|------|------|
| **严重程度** | 🟡 中危（Medium） |
| **置信度** | ⚠️ 可能（Probable） |
| **OWASP** | A01:2021 – 访问控制失效 |
| **STRIDE** | Tampering |
| **文件** | `src/manager/medical_history_attachment_manager.py` |
| **行号** | `get_full_path()` |

**描述**：
`get_full_path()` 方法将 `storage_key` 直接传给 `Path(storage_key)` 而未调用 `.resolve()` 进行路径规范化。虽然 `build_storage_key()` 使用了 `secure_filename()` + `uuid4().hex`，但若 `storage_key` 字段在数据库中被篡改（例如通过 SQL 注入或直接数据库访问），攻击者可能通过 `..` 跳出预期目录。

**证据**：
```python
# src/manager/medical_history_attachment_manager.py
def get_full_path(self):
    return self._base_dir() / Path(self.storage_key)
    # 缺少: .resolve() 并验证结果在 _base_dir() 之内
```

**修复建议**：
```python
def get_full_path(self):
    full = (self._base_dir() / Path(self.storage_key)).resolve()
    base = self._base_dir().resolve()
    if not str(full).startswith(str(base)):
        raise ValueError("Path traversal detected")
    return full
```

---

### R — Repudiation（否认性）

> 本次审计未发现独立的 R 类漏洞，但以下设计存在审计能力不足的问题，相关改进项已在 I-04/I-05 信息类条目中合并说明。

---

### I — Information Disclosure（信息泄露）

---

#### [I-03] JWT Token 存储于 localStorage，可被 XSS 窃取

| 字段 | 详情 |
|------|------|
| **严重程度** | 🟠 高危（High） |
| **置信度** | ✅ 已确认 |
| **OWASP** | A07:2021 – 身份认证与认证失败 |
| **STRIDE** | Information Disclosure / Spoofing |
| **文件** | `frontend/src/utils/auth.js` |
| **行号** | L19–L20 |

**描述**：
Access Token 与 Refresh Token 均存储于 `localStorage`。任何成功的 XSS 攻击（如来自第三方依赖、iframe 内容、DOM-based XSS）均可通过 `localStorage.getItem('access_token')` 直接窃取令牌，实现会话劫持。

**证据**：
```javascript
// frontend/src/utils/auth.js L19-20
localStorage.setItem('access_token', accessToken);
localStorage.setItem('refresh_token', refreshToken);
```

**修复建议**：
- 将 Refresh Token 改为 `httpOnly; Secure; SameSite=Strict` Cookie 存储，彻底杜绝 JS 可访问。
- Access Token 可保留内存（React state / context），不持久化，页面刷新后通过 silent refresh Cookie 恢复。
- 若暂无法改 Cookie，至少启用 CSP（见 T-07）降低 XSS 攻击面。

---

#### [I-04] 内部异常 `str(e)` 直接返回客户端（多处泄露）

| 字段 | 详情 |
|------|------|
| **严重程度** | 🟠 高危（High） |
| **置信度** | ✅ 已确认 |
| **OWASP** | A05:2021 – 安全误配置 |
| **STRIDE** | Information Disclosure |
| **文件** | `src/service/threshold_service.py`（L62, L99, L125, L181, L228）<br>`src/service/health_service.py`（L873） |

**描述**：
多处以 `"details": str(e)` 的形式将内部 Python 异常（包含堆栈框架、SQL 表名、文件路径等）直接暴露在 HTTP 响应体中，向攻击者提供了枚举内部系统结构的能力。

**证据**：
```python
# src/service/threshold_service.py L62
return jsonify({
    "error": "Failed to create draft",
    "details": str(e)   # 将完整异常信息返回给客户端
}), 500

# src/service/health_service.py L873
return jsonify(error("500", f"Failed to process file: {str(e)}")), 500
```

**修复建议**：
- 所有 500 类错误只返回通用消息，如 `"An internal error occurred"` 或包含 request_id 的参考码。
- 真实异常信息通过结构化日志（如 structlog）记录到服务端，不流向客户端。
- 使用全局 Flask `@app.errorhandler(Exception)` 统一处理未捕获异常。

---

#### [I-05] Admin 密码重置接口明文返回临时密码

| 字段 | 详情 |
|------|------|
| **严重程度** | 🟠 高危（High） |
| **置信度** | ✅ 已确认 |
| **OWASP** | A02:2021 – 密码学失败 |
| **STRIDE** | Information Disclosure |
| **文件** | `src/service/admin_service.py` |
| **行号** | L90 |

**描述**：
Admin 的密码重置接口在 HTTP 响应体中直接返回明文临时密码 `"temp_password": temp_password`。在 HTTP（非 HTTPS）环境下可被网络嗅探，同时也记录在代理日志、监控系统和浏览器开发工具的网络面板中。

**证据**：
```python
# src/service/admin_service.py L90
return jsonify({
    "message": "Password reset successfully",
    "temp_password": temp_password  # 明文临时密码
}), 200
```

**修复建议**：
- 短期：仅在严格 HTTPS 下提供此接口，并在访问日志中消除响应体记录。
- 长期：考虑通过带外（邮件/短信）通知临时密码，而非 HTTP 响应体。
- 若必须在响应中返回，设置 `Cache-Control: no-store` 并在 API 文档中标注敏感信息处理要求。

---

#### [I-16] 缺少 `.env.example` 配置引导文件

| 字段 | 详情 |
|------|------|
| **严重程度** | 🔵 低危（Low） |
| **置信度** | ✅ 已确认 |
| **OWASP** | A05:2021 – 安全误配置 |
| **STRIDE** | Information Disclosure |
| **文件** | 项目根目录 / `docs/` |

**描述**：
项目根目录不存在 `.env.example` 文件，开发者缺乏安全配置的参考模板，容易在配置时遗漏关键密钥项，使用弱默认值部署到生产环境。

**修复建议**：
创建 `.env.example`，列出所有必需环境变量（占位值，非真实密钥）：
```
JWT_SECRET_KEY=<change-me-use-openssl-rand-hex-32>
SECRET_KEY=<change-me-use-openssl-rand-hex-32>
SQLALCHEMY_DATABASE_URI=mysql+pymysql://user:password@host/dbname
MYSQL_SSL=1
MYSQL_SSL_CA=/path/to/ca.pem
SUPER_ADMIN_PASSWORD=<strong-password-here>
CORS_ORIGINS=https://yourdomain.com
```

---

#### [I-17] 前端 `console.error` 可能泄露调试信息 ⚪

| 字段 | 详情 |
|------|------|
| **严重程度** | ⚪ 信息（Informational） |
| **置信度** | 🔍 可能（Possible） |
| **OWASP** | A09:2021 – 安全日志与监控失败 |
| **STRIDE** | Information Disclosure |
| **文件** | `frontend/src/pages/Login.js` 等 |

**描述**：
前端多处使用 `console.error('Login error:', error)` 输出错误详情到浏览器控制台。在生产环境中，若 error 对象包含服务端响应细节（如后端堆栈、SQL 信息），可被用户或安全研究人员查看。

**修复建议**：
- 生产环境通过 `webpack.DefinePlugin` 或条件编译禁用 `console.error` / `console.log`。
- 或将敏感字段从 axios 响应中剔除后再记录日志。

---

#### [I-18] 批量导入行级错误包含内部字段名与行索引 ⚪

| 字段 | 详情 |
|------|------|
| **严重程度** | ⚪ 信息（Informational） |
| **置信度** | ✅ 已确认 |
| **OWASP** | A09:2021 – 安全日志与监控失败 |
| **STRIDE** | Information Disclosure |
| **文件** | `src/service/health_service.py` |
| **行号** | L767 |

**描述**：
`row_errors.append(f"Unexpected error: {str(e)}")` 在批量导入时将内部字段名、行索引等信息作为错误列表返回给客户端，虽对普通用户有帮助，但也向外暴露内部数据结构。

**修复建议**：
- 对"意外异常"类错误，仅返回行号 + 通用消息 `"Unexpected error at row N, please check data format"`，不暴露具体异常字符串。

---

### D — Denial of Service（拒绝服务）

---

#### [D-09] xlsx 批量导入无 ZIP bomb / 内存炸弹防护

| 字段 | 详情 |
|------|------|
| **严重程度** | 🟡 中危（Medium） |
| **置信度** | ⚠️ 可能（Probable） |
| **OWASP** | A04:2021 – 不安全设计 |
| **STRIDE** | Denial of Service |
| **文件** | `src/service/health_service.py` |
| **行号** | L596 |

**描述**：
批量导入通过 `pd.read_excel(file, engine='openpyxl')` 解析 xlsx 文件。xlsx 是 ZIP 包格式，openpyxl 在解压时无法预先检测 ZIP bomb（压缩炸弹）。攻击者可构造一个小于 5 MB 的 xlsx 文件，但解压后内容数百 MB，可导致服务内存耗尽。虽已有 5 MB 文件大小限制和 1000 行后处理限制，但行数限制在解析之后才生效。

**证据**：
```python
# src/service/health_service.py L596
df = pd.read_excel(file, engine='openpyxl')
# 1000 行限制在此行之后才截断，openpyxl 已完成完整解压
```

**修复建议**：
- 在调用 `pd.read_excel` 之前，先检测文件中的 ZIP 条目解压大小（`zipfile.ZipFile` + 统计 `ZipInfo.file_size`）。
- 设置最大解压大小阈值（如 50 MB），超出则拒绝。
- 或改用 `pd.read_excel(..., nrows=1001)` 限制 pandas 读取行数，仅可部分缓解。

---

### E — Elevation of Privilege（权限提升）

---

#### [E-12] Admin 服务 `_require_role()` 不验证 token_version（角色降级无效窗口期）

| 字段 | 详情 |
|------|------|
| **严重程度** | 🟡 中危（Medium） |
| **置信度** | ⚠️ 可能（Probable） |
| **OWASP** | A01:2021 – 访问控制失效 |
| **STRIDE** | Elevation of Privilege |
| **文件** | `src/service/admin_service.py` |
| **行号** | `_require_role()` 函数 |

**描述**：
`admin_service.py` 中的 `_require_role()` 仅从 JWT claims 中读取角色，不实时查询数据库验证 `token_version`。这意味着如果超级管理员降级了一个 Admin 用户，该 Admin 的 Access Token 在过期前（默认 10 分钟）仍然有效，可以继续调用管理接口。

**证据**：
```python
# src/service/admin_service.py _require_role()
role = get_jwt()["role"]  # 仅读取声明角色
if role not in allowed_roles:
    abort(403)
# 未验证：User.token_version == JWT claims 中的 token_version
```

**修复建议**：
- 在 `_require_role()` 中增加 `token_version` 实时校验（类比 `auth_service.py` 中的做法）。
- 或将 Access Token 有效期进一步缩短至 5 分钟，降低窗口期风险。
- 实施 admin 操作前可强制重新验证（缩短超时或要求二次鉴权）。

---

## 依赖组件漏洞摘要

> 以下基于 `requirements.txt` 已知版本进行静态依赖分析，未实施动态 CVE 扫描。建议执行 `pip audit` 或 `safety check` 获取完整报告。

| 包 | 当前版本 | 已知风险 | 建议 |
|----|---------|---------|------|
| Flask | 3.0.3 | 最新稳定，暂无已知高危 CVE | 关注官方安全公告 |
| Flask-JWT-Extended | 4.6.0 | 暂无已知高危 CVE | 监控 JWT alg confusion 相关更新 |
| gunicorn | 21.2.0 | CVE-2024-1135（HTTP 请求走私）已在 22.0.0 修复 | 🟠 建议升级至 22.0.0 或以上 |
| pandas | 未固定版本 | 历史存在 CSV 注入、XXE 风险 | 固定版本 + 定期更新 |
| openpyxl | 未固定版本 | ZIP bomb 风险（从代码层面缓解更有效） | 实施代码层 ZIP 大小检测 |
| PyMySQL | 1.1.1 | 暂无已知高危 CVE | 保持更新 |

**⚠️ 高优先级**：Gunicorn 21.2.0 存在 CVE-2024-1135，允许 HTTP 请求走私攻击，应升级至 22.0.0+。

---

## 修复优先级矩阵

| 优先级 | 编号 | 标题 | 严重程度 | 修复工作量 |
|--------|------|------|----------|----------|
| P0（立即修复） | S-01 | JWT/Session 弱默认密钥 | 🔴 Critical | 低（修改配置） |
| P0（立即修复） | S-06 | SUPER_ADMIN 弱默认密码 | 🟠 High | 低（修改配置） |
| P0（立即修复） | I-04 | 内部异常 str(e) 泄露 | 🟠 High | 低（错误处理重构） |
| P1（本次发布前） | S-02 | docker-compose 硬编码凭据 | 🟠 High | 低（移除默认值） |
| P1（本次发布前） | I-03 | JWT 存储于 localStorage | 🟠 High | 高（架构级调整） |
| P1（本次发布前） | I-05 | Admin 明文临时密码响应 | 🟠 High | 低（HTTPS + 日志处理） |
| P1（本次发布前） | T-07 | 缺少安全 HTTP 响应头 | 🟡 Medium | 低（集成 Flask-Talisman） |
| P1（本次发布前） | gunicorn | CVE-2024-1135 HTTP 请求走私 | 🟠 High | 低（升级版本） |
| P2（下个 Sprint） | S-08 | IP 速率限制可被绕过 | 🟡 Medium | 中 |
| P2（下个 Sprint） | D-09 | xlsx 无 ZIP bomb 防护 | 🟡 Medium | 低（增加 ZIP 大小预检） |
| P2（下个 Sprint） | T-10 | MySQL SSL 无 CA 验证 | 🟡 Medium | 低（配置 CA 证书） |
| P2（下个 Sprint） | T-11 | 附件路径无规范化 | 🟡 Medium | 低（增加 resolve + 前缀校验） |
| P2（下个 Sprint） | E-12 | Admin role 不验 token_version | 🟡 Medium | 中 |
| P2（下个 Sprint） | S-13 | SECRET_KEY 共享弱默认回退 | 🟡 Medium | 低（拆分环境变量） |
| P3（技术债 Backlog） | S-14 | 密码强度不足 | 🔵 Low | 低 |
| P3（技术债 Backlog） | S-15 | 注册邮箱枚举 | 🔵 Low | 低 |
| P3（技术债 Backlog） | I-16 | 缺少 .env.example | 🔵 Low | 低 |
| P3（技术债 Backlog） | I-17 | 前端 console.error | ⚪ Info | 低 |
| P3（技术债 Backlog） | I-18 | 批量导入行级错误暴露 | ⚪ Info | 低 |

---

## 方法论说明

- **分析类型**：静态代码分析（SAST）
- **动态测试**：本次未执行 DAST。建议使用 OWASP ZAP 进行运行时验证，重点测试：JWT 伪造、路径遍历、ZIP bomb、速率限制绕过。
- **范围排除项**：
  - E2E 测试脚本（`tests/e2e/`）
  - 部署脚本安全性（`deploy/`、`scripts/`）
  - Kubernetes RBAC 与网络策略
  - 基础设施层（Azure、K8s 节点安全）
- **威胁模型**：假设攻击者为已注册普通用户，并可尝试权限提升；同时考虑外部未认证攻击者。

---

## 下一步行动

1. **立即（P0）**：由 Developer Agent 修复 S-01（移除弱默认密钥）、S-06（生产密码强制配置）、I-04（异常信息泄露统一处理）。
2. **代码审查**：对 I-03（localStorage JWT）进行专项架构讨论，评估迁移 httpOnly Cookie 方案。
3. **依赖升级**：将 `gunicorn >= 22.0.0` 纳入下次 `requirements.txt` 更新。
4. **配置治理**：新建 `.env.example`（I-16），删除 `docker-compose.yml` 中所有硬编码凭据（S-02）。
5. **代码扫描**：将 `pip audit`、`bandit -r src/` 纳入 CI 流水线。

---

*由 Security_Tester Agent 生成 | 模型：GitHub Copilot (Claude Sonnet 4.6) | 健康记录平台安全计划*
*报告路径：`docs/security/audit-report-20260311.md`*
