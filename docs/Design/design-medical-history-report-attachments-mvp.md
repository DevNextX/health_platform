# Design: 病史附件 MVP（上传/列表/下载/删除）

## 1. Overview
- Reference: [需求文档](../requirements/req-medical-history-report-attachments-mvp.md)
- 目标：为既往病史条目提供“附件闭环能力”（上传/列表/下载/删除），支持图片、Word、PDF，并保持成员隔离与现有 MedicalHistory 主流程兼容。
- 新增业务约束：每条既往病史记录最多保留 10 个有效附件；删除后释放名额。
- 范围边界：本期不做 OCR、不做全文检索、不做跨病史聚合导出。

## 2. 现状与差距

### 2.1 当前现状（代码基线）
- 后端已有病史主实体与 CRUD：
  - Model: `MedicalHistory`（`src/models.py`）
  - Manager: `MedicalHistoryManager`（`src/manager/medical_history_manager.py`）
  - Service: `medical_history_service.py`（`/api/v1/medical-history`）
- 前端已有 `MedicalHistory` 页面与 API 封装：
  - 页面：`frontend/src/pages/MedicalHistory.js`
  - API：`frontend/src/services/api.js` 中 `medicalHistoryAPI`
- 已有成员权限主链路（`MemberManager.get_member/get_household`）可复用。

### 2.2 关键差距
1. **无附件数据模型**：当前无病史附件表、无附件元数据持久化。
2. **无文件存储抽象**：当前项目未形成可切换的文件存储适配层（local/object storage）。
3. **无附件 API**：缺少上传、列表、下载、删除接口。
4. **Service 分层不完全一致**：现有 `medical_history_service` 在 update/delete 中直接查询 `MedicalHistory`，不满足“Service -> Manager -> Models”约束；附件功能必须严格执行分层，并建议顺带收敛该问题。
5. **前端无附件交互**：缺少上传控件、附件列表、下载/删除操作及状态提示。

---

## 3. Architecture Changes

### 3.1 Backend
新增模块（按分层）：
- **Models**
  - `MedicalHistoryAttachment`
  - （可选但推荐）`MedicalHistoryAttachmentAuditLog`
- **Manager**
  - `MedicalHistoryAttachmentManager`：附件元数据 CRUD、权限范围查询、软删除/硬删除执行、审计落库。
  - `AttachmentStorageManager`：统一文件存储门面，路由到 `LocalAttachmentStorage` 或 `ObjectAttachmentStorage`。
  - 对现有 `MedicalHistoryManager` 补充 `get_by_id_and_household(...)` 等方法，避免 service 直接查库。
- **Service**
  - 新增 `medical_history_attachment_service.py` Blueprint，建议挂载到 `/api/v1/medical-history` 前缀下。
  - 所有权限、参数校验、响应组装在 Service；所有数据访问由 Manager 负责。

### 3.2 Frontend
- 在 `MedicalHistory` 页面中扩展“附件区块”：
  - 上传按钮（支持多次单文件上传）
  - 列表展示（文件名、大小、类型、上传时间、上传人）
  - 下载、删除动作
- 在 `api.js` 新增 `medicalHistoryAttachmentAPI`。
- 新增中英文 i18n key（文案、错误提示、确认提示）。

---

## 4. 数据模型设计（建议表结构与索引）

## 4.1 表：`medical_history_attachments`
- `id` BIGINT / Integer PK
- `household_id` Integer, FK -> `households.id`, not null（便于权限过滤）
- `member_id` Integer, FK -> `members.id`, not null（便于成员维度过滤）
- `medical_history_id` Integer, FK -> `medical_histories.id`, not null
- `file_name` VARCHAR(255), not null（原始文件名）
- `file_ext` VARCHAR(16), not null（如 `.pdf/.docx/.jpg`）
- `mime_type` VARCHAR(128), not null
- `file_size` BIGINT, not null
- `storage_provider` VARCHAR(32), not null（`local` / `s3` / `oss`）
- `storage_key` VARCHAR(512), not null（对象路径/对象键）
- `storage_bucket` VARCHAR(128), nullable（对象存储可用）
- `sha256` CHAR(64), nullable（后续去重/审计）
- `status` VARCHAR(16), not null, default `active`（`active` / `deleted`）
- `created_by_user_id` Integer, FK -> `users.id`, not null
- `deleted_by_user_id` Integer, FK -> `users.id`, nullable
- `created_at` DATETIME, not null
- `deleted_at` DATETIME, nullable

> MVP 建议“逻辑删除元数据 + 物理删除文件（异步可选）”。若实现复杂度受限，可先硬删除元数据+文件，但需保留审计日志。

## 4.2 索引建议
- `idx_mha_history_created`：`(medical_history_id, created_at DESC)`（附件列表主路径）
- `idx_mha_member_created`：`(member_id, created_at DESC)`（成员维度统计/扩展）
- `idx_mha_household_status`：`(household_id, status)`（权限与可见性过滤）
- `uk_mha_storage_key`：`(storage_key)` 唯一（防止重复引用错误）
- （可选）`idx_mha_sha256`：`(sha256)`（后续秒传/去重预留）

## 4.3 审计表（推荐）`medical_history_attachment_audit_logs`
- `id`, `attachment_id`, `action`(`upload|download|delete`), `actor_user_id`, `trace_id`, `metadata_json`, `created_at`
- 用于满足“敏感健康资料”操作可追踪。

---

## 5. 存储抽象设计（local + 对象存储可切换）

### 5.1 抽象接口
定义统一接口（位于 manager 层，避免 service 感知底层）：
- `save(file_stream, *, key, content_type) -> SaveResult`
- `open_download_stream(storage_key) -> (stream, content_type, content_length)`
- `delete(storage_key) -> None`
- `exists(storage_key) -> bool`

### 5.2 Provider 设计
- `LocalAttachmentStorage`
  - 基于本地目录（如 `instance/uploads/medical-history/`）
  - 通过 `send_file` 或 streaming response 下载
- `ObjectAttachmentStorage`
  - 兼容 S3 协议（MinIO/S3/OSS 统一抽象）
  - MVP 可先返回后端转发流；后续可演进预签名 URL

### 5.3 配置开关
在 `src/config.py` 增加：
- `ATTACHMENT_STORAGE_PROVIDER=local|s3`
- `ATTACHMENT_LOCAL_BASE_PATH=instance/uploads`
- `ATTACHMENT_MAX_FILES_PER_HISTORY=10`
- `ATTACHMENT_MAX_FILE_SIZE_MB=20`（建议默认 20MB）
- `ATTACHMENT_ALLOWED_EXT=.jpg,.jpeg,.png,.pdf,.doc,.docx`
- 对象存储参数：`ATTACHMENT_S3_ENDPOINT/BUCKET/ACCESS_KEY/SECRET_KEY/REGION`

### 5.4 路径命名规则
`medical-history/{household_id}/{member_id}/{medical_history_id}/{yyyy}/{mm}/{uuid}_{safe_filename}`

---

## 6. API 设计（请求/响应、错误码、权限校验）

统一前缀：`/api/v1/medical-history`

## 6.1 上传附件
- `POST /api/v1/medical-history/{history_id}/attachments`
- `Content-Type: multipart/form-data`
- Form 字段：`file`

权限校验：
1. JWT 登录
2. 校验 `history_id` 属于当前用户 household（通过 manager，不在 service 直接查库）
3. 校验该病史关联成员可访问
4. 校验该病史当前有效附件数 `< 10`；达到上限时拒绝上传

成功响应 `201`：
```json
{
  "id": 123,
  "medical_history_id": 88,
  "file_name": "CT报告.pdf",
  "mime_type": "application/pdf",
  "file_size": 345678,
  "created_at": "2026-01-01T10:00:00Z"
}
```

达到上限响应 `400`：
```json
{
  "code": "400",
  "message": "Attachment count exceeds 10 per medical history",
  "details": {
    "file": [
      "maximum 10 attachments allowed per medical history"
    ]
  }
}
```

## 6.2 附件列表
- `GET /api/v1/medical-history/{history_id}/attachments?page=1&size=20`
- 返回：
```json
{
  "attachments": [ ... ],
  "pagination": {"page":1,"size":20,"total":3,"pages":1}
}
```

## 6.3 下载附件
- `GET /api/v1/medical-history/{history_id}/attachments/{attachment_id}/download`
- 返回文件流，header 包含：
  - `Content-Type`
  - `Content-Disposition: attachment; filename*=UTF-8''...`

## 6.4 删除附件
- `DELETE /api/v1/medical-history/{history_id}/attachments/{attachment_id}`
- 成功 `200`：`{"message":"Attachment deleted"}`

## 6.5 错误码（建议）
遵循现有 `error(code, message, details)` 结构：
- `400` 参数错误（缺少文件、扩展名不支持、大小超限）
- `401` 未认证
- `403` 无权限（可选）
- `404` 病史或附件不存在/不可访问
- `409` 状态冲突（例如重复删除）
- `415` 不支持的媒体类型
- `500` 内部错误

建议细分业务 code：
- `ATTACHMENT_FILE_REQUIRED`
- `ATTACHMENT_TYPE_NOT_ALLOWED`
- `ATTACHMENT_SIZE_EXCEEDED`
- `ATTACHMENT_COUNT_EXCEEDED`
- `ATTACHMENT_NOT_FOUND`
- `ATTACHMENT_ACCESS_DENIED`

---

## 7. 分层约束（强制）
- Service 层仅做：鉴权、参数校验、调用 manager、构造 HTTP 响应。
- Service 层**不得**直接 `Model.query` 或 `db.session`。
- Manager 层负责：
  - 病史归属查询（含 household/member）
  - 附件元数据持久化
  - 存储适配调用
  - 事务边界与重试策略
- Models 层仅定义实体与关系。

> 本需求建议同时修正现有 `medical_history_service.py` 的直接查库路径（update/delete），统一迁移到 `MedicalHistoryManager`。

---

## 8. 安全与合规
- **类型控制**：扩展名 + MIME 双校验；禁止可执行脚本类文件。
- **大小控制**：单文件大小限制（默认 20MB，可配置）。
- **数量控制**：单条病史最多 10 个有效附件，服务端校验为准，前端仅做体验增强。
- **文件名安全**：规范化文件名，移除路径穿越字符。
- **鉴权隔离**：以 household + member + history 三重约束校验。
- **下载鉴权**：每次下载实时鉴权，不返回可长期复用的公开 URL。
- **审计**：记录 upload/download/delete 行为（用户、时间、对象、trace_id）。
- **删除策略**：删除后不可直接下载；列表不可见。
- **合规提示**：前端增加“医疗资料敏感信息提示”。

---

## 9. 前端交互设计与 i18n 影响

## 9.1 交互流程
1. 用户在病史行点击“附件管理”进入 Drawer/Modal（MVP 推荐 Drawer，减少页面跳转）。
2. 顶部 Upload 按钮：
   - 上传前校验类型/大小
  - 展示当前附件数与剩余可上传数量，例如 `3 / 10`
  - 当附件数达到 10 时禁用上传按钮，并显示“已达上限”提示
   - 上传中显示进度与禁用状态
3. 列表区展示：文件名、类型图标、大小、上传时间、操作（下载/删除）。
4. 删除需二次确认（不可恢复提示）。
5. 所有失败态展示明确原因（类型不支持、超限、网络失败、权限失效）。

## 9.2 i18n 新增 key（示例）
- `medicalHistory.attachments.title`
- `medicalHistory.attachments.upload`
- `medicalHistory.attachments.empty`
- `medicalHistory.attachments.typeNotAllowed`
- `medicalHistory.attachments.sizeExceeded`
- `medicalHistory.attachments.deleteConfirm`
- `medicalHistory.attachments.downloadFail`
- `medicalHistory.attachments.deleteFail`

中英文均需补齐，遵循现有 `translation.json` 结构。

---

## 10. 测试策略（后端 / 前端 / E2E）

## 10.1 后端（Pytest）
新增 `tests/test_medical_history_attachments.py`：
- 上传成功（图片、pdf、docx）
- 不支持类型上传失败
- 超大小上传失败
- 第 11 个附件上传失败，并返回明确错误信息
- 越权 history_id 上传/列表/下载/删除均拒绝
- 列表只返回当前病史附件
- 删除后不可下载
- 存储失败回滚（元数据与文件一致性）
- 审计日志写入验证（若本期实现）

## 10.2 前端（组件/集成）
- 上传组件校验逻辑
- 达到 10 个附件时上传按钮禁用与提示文案
- 上传成功后列表刷新
- 删除确认与删除后 UI 更新
- 错误提示映射后端 message/code
- i18n 文案渲染（zh/en）

## 10.3 E2E（Playwright）
- 登录 -> 选择成员A -> 新建病史 -> 上传附件 -> 列表可见 -> 下载成功 -> 删除后消失
- 连续上传 10 个附件后，第 11 个附件被阻止上传
- 切换成员B，确认无法看到成员A附件
- token 过期后重试流程（401->refresh）附件接口可恢复

---

## 11. 演进路径（后续能力）
- **检索增强**：按文件名、时间范围、类型过滤；后续引入 OCR/全文索引。
- **个人维度汇总**：跨病史聚合查看附件时间线。
- **导出能力**：按成员/时间范围导出 ZIP，支持病史摘要 + 附件打包。
- **对象存储优化**：预签名 URL、分片上传、大文件断点续传。
- **合规增强**：病毒扫描、DLP 分类、下载水印/审计告警。

---

## 12. High-Level Task Blocks
- [ ] Database Migration
  - [ ] 新增 `medical_history_attachments` 表与索引
  - [ ] （可选）新增附件审计日志表
- [ ] Backend Service Logic
  - [ ] 新增 `MedicalHistoryAttachmentManager`
  - [ ] 新增存储抽象与 local/object provider
  - [ ] 新增附件 API（上传/列表/下载/删除）
  - [ ] 修正 medical_history service 直接查库问题，统一走 manager
- [ ] Frontend Integration
  - [ ] `medicalHistoryAttachmentAPI` 接口封装
  - [ ] `MedicalHistory` 页面新增附件管理 UI
  - [ ] zh/en i18n 文案补充
- [ ] Security & Compliance
  - [ ] 类型/大小/文件名安全校验
  - [ ] 审计日志与越权拦截验证
- [ ] Testing & Verification
  - [ ] 后端 pytest
  - [ ] 前端组件/集成测试
  - [ ] Playwright E2E 闭环
