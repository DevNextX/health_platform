# Implementation Plan: 既往病史检查报告附件闭环（MVP）

## References
- Requirement: `docs/requirements/req-medical-history-report-attachments-mvp.md`
- Design: `docs/design/design-medical-history-report-attachments-mvp.md`
- 现有代码基线：
  - Backend: `src/models.py`, `src/manager/medical_history_manager.py`, `src/service/medical_history_service.py`, `src/app.py`, `src/config.py`
  - Frontend: `frontend/src/pages/MedicalHistory.js`, `frontend/src/services/api.js`, `frontend/src/i18n/locales/{zh,en}/translation.json`
  - Tests: `tests/test_medical_history.py`, `tests/e2e/`

## API 契约落地顺序（先后端契约，后前端接入）
1. **Step A（只定义，不联调）**：确定附件 4 个接口与错误码（upload/list/download/delete），先补充后端测试用例骨架。
2. **Step B（后端可用）**：完成 API + 权限 + 存储 + 迁移，确保 `pytest` API 测试通过。
3. **Step C（前端接入）**：`api.js` 增加附件 API，`MedicalHistory` 页面接入 Drawer/Modal 附件区块。
4. **Step D（端到端）**：补 E2E 闭环（上传→列表→下载→删除→成员隔离）。

## 测试优先级与回归范围
- **P0（必须先过）**
  - 后端：附件上传/列表/下载/删除、越权访问、类型/大小校验。
  - 前端：附件上传前校验、错误提示、删除确认、列表刷新。
- **P1（同版本完成）**
  - 存储失败回滚一致性（元数据与文件）。
  - i18n 中英文文案完整性与回退行为。
- **P2（回归增强）**
  - token 刷新后附件接口重试流程。
  - 大量附件场景（分页/性能）基础验证。

**回归范围（必须执行）**
- 后端：`tests/test_medical_history.py`、新增 `tests/test_medical_history_attachments.py`、鉴权相关测试。
- 前端：`MedicalHistory` 页面新增/编辑/删除原流程、成员切换流程、上传组件行为。
- E2E：成员 A/B 隔离、下载行为、删除后不可下载。

---

## Phase 1：数据库迁移（Schema & 索引）

### 目标
建立附件元数据持久化能力，支持病史-附件关联、权限过滤与后续审计扩展。

### 涉及文件
- `src/models.py`
- `migrations/versions/<new_revision>_medical_history_attachments.py`
- （可选）`migrations/versions/<new_revision>_medical_history_attachment_audit_logs.py`

### 关键实现点
- [ ] **Task 1.1**：新增 `MedicalHistoryAttachment` 模型（household_id/member_id/medical_history_id/file_name/file_ext/mime_type/file_size/storage_provider/storage_key/status/created_at/deleted_at 等）。
- [ ] **Task 1.2**：增加关系与索引（`medical_history_id + created_at`，`household_id + status`，`storage_key` 唯一）。
- [ ] **Task 1.3**：生成 Alembic 迁移并验证可前后迁移（upgrade/downgrade）。
- [ ] **Task 1.4（可选）**：新增审计表 `medical_history_attachment_audit_logs`（upload/download/delete）。

### 风险
- SQLite/MySQL 在索引、字段长度、默认值上的兼容差异。
- 历史环境存在 `db.create_all()` 路径，迁移与自动建表并存可能引发漂移。

### 完成定义（DoD）
- 迁移脚本可执行，`upgrade` 后可见新表和索引，`downgrade` 可回滚。
- 模型字段与设计文档一致，无 service 直连 DB 变更。

---

## Phase 2：后端实现（Manager/Storage/Service）

### 目标
提供可用且权限隔离正确的附件 API，并保持 Flask + SQLAlchemy 分层约束。

### 涉及文件
- `src/manager/medical_history_attachment_manager.py`（新增）
- `src/manager/attachment_storage_manager.py`（新增）
- `src/manager/medical_history_manager.py`（增强：`get_by_id_and_household` 等）
- `src/service/medical_history_attachment_service.py`（新增）
- `src/service/medical_history_service.py`（修正 update/delete 直查模型）
- `src/config.py`（附件配置项）
- `src/app.py`（注册附件 Blueprint）

### 关键实现点
- [ ] **Task 2.1**：实现存储抽象（local provider 起步，接口统一 save/open/delete/exists）。
- [ ] **Task 2.2**：实现附件 manager：元数据创建、分页查询、删除、权限范围校验（household/member/history 三重约束）。
- [ ] **Task 2.2.1**：增加单条病史最多 10 个有效附件的后端校验，并支持删除后释放名额。
- [ ] **Task 2.3**：实现 API：
  - `POST /api/v1/medical-history/{history_id}/attachments`
  - `GET /api/v1/medical-history/{history_id}/attachments`
  - `GET /api/v1/medical-history/{history_id}/attachments/{attachment_id}/download`
  - `DELETE /api/v1/medical-history/{history_id}/attachments/{attachment_id}`
- [ ] **Task 2.4**：实现类型+MIME+大小校验，统一错误码（`ATTACHMENT_FILE_REQUIRED` 等）。
- [ ] **Task 2.5**：修正 `medical_history_service.py` 中 update/delete 直接 `Model.query`，统一走 manager。

### 风险
- 上传成功但元数据写入失败（或相反）造成不一致。
- 下载头 `Content-Disposition` 对中文文件名兼容问题。
- 鉴权遗漏导致跨家庭成员越权访问。

### 完成定义（DoD）
- 4 个 API 可用且权限隔离正确（含越权拒绝）。
- service 层不直接 `Model.query` / `db.session`。
- 上传/删除失败路径有可追踪日志与明确错误响应。

---

## Phase 3：前端实现（React + AntD + i18n）

### 目标
在现有 `MedicalHistory` 页面内提供附件管理闭环，不破坏已有病史 CRUD 体验。

### 涉及文件
- `frontend/src/services/api.js`
- `frontend/src/pages/MedicalHistory.js`
- `frontend/src/i18n/locales/zh/translation.json`
- `frontend/src/i18n/locales/en/translation.json`

### 关键实现点
- [ ] **Task 3.1**：新增 `medicalHistoryAttachmentAPI`（upload/list/download/remove）。
- [ ] **Task 3.2**：在病史行操作中新增“附件管理”入口（Drawer/Modal），显示列表与操作按钮。
- [ ] **Task 3.3**：上传前前端校验（扩展名、大小、数量上限），上传中状态与失败提示。
- [ ] **Task 3.4**：下载动作使用 blob 流处理，保留文件名。
- [ ] **Task 3.5**：删除增加二次确认，成功后刷新当前附件列表。
- [ ] **Task 3.6**：补全中英文 i18n key，保证报错文案可理解且与后端错误码映射。
- [ ] **Task 3.7**：在附件抽屉中展示当前数量与上限，达到 10 个时禁用上传入口。

### 风险
- 现有 `MedicalHistory` 页面已较长，直接扩展可能导致组件过重。
- 浏览器下载行为差异（尤其移动端/不同内核）。

### 完成定义（DoD）
- 用户可在同一页面完成上传/查看/下载/删除闭环。
- 切换病史条目仅显示对应附件。
- 中英文文案齐全且无硬编码中文残留。

---

## Phase 4：测试与验收（Backend + Frontend + E2E）

### 目标
通过自动化测试证明功能正确、安全隔离、且不回归既有病史功能。

### 涉及文件
- `tests/test_medical_history_attachments.py`（新增）
- `tests/test_medical_history.py`（回归补充）
- `frontend/src/pages/__tests__/MedicalHistory*.test.js`（如项目已有单测体系则新增）
- `tests/e2e/`（新增或扩展附件场景）

### 关键实现点
- [ ] **Task 4.1（P0）**：后端 pytest：上传成功（jpg/pdf/docx）、类型不支持、超大小、越权拒绝、删除后不可下载。
- [ ] **Task 4.1.1（P0）**：补充第 11 个附件上传失败用例，验证错误码/提示文案。
- [ ] **Task 4.2（P0）**：前端集成测试：上传前校验、上传成功后刷新、删除确认、错误提示映射。
- [ ] **Task 4.2.1（P0）**：补充达到 10 个附件时上传按钮禁用与提示测试。
- [ ] **Task 4.3（P1）**：异常一致性：存储失败回滚、重复删除冲突处理。
- [ ] **Task 4.4（P0）**：E2E：登录→成员A病史上传→列表可见→下载→删除→成员B不可见。
- [ ] **Task 4.4.1（P0）**：E2E 验证连续上传 10 个附件后，第 11 个附件被前后端共同阻止。
- [ ] **Task 4.5**：执行回归命令并留存结果：
  - `python -m pytest tests/test_medical_history.py -v`
  - `python -m pytest tests/test_medical_history_attachments.py -v`
  - `python -m pytest tests/ -v`（至少相关模块）
  - `frontend npm test`（相关用例）

### 风险
- 测试环境文件系统路径在 CI 与本地不一致导致 flaky。
- E2E 下载校验在不同运行器表现差异。

### 完成定义（DoD）
- P0 用例 100% 通过，P1 无阻塞缺陷。
- 回归范围执行完成且无高优先级回归。
- 验收项 AC1~AC8 均有对应测试或手工验收证据。

---

## Phase 5：发布与回滚

### 目标
平滑上线附件能力，可快速止损回滚，避免影响主病史流程。

### 涉及文件
- `src/config.py`（上线配置）
- 部署配置（环境变量注入位置：CI/CD 或运行环境）
- 运维文档：`docs/ops/`（新增上线与回滚说明，若当前迭代要求）

### 关键实现点
- [ ] **Task 5.1**：配置上线：`ATTACHMENT_STORAGE_PROVIDER`、`ATTACHMENT_LOCAL_BASE_PATH`、`ATTACHMENT_MAX_FILE_SIZE_MB`、`ATTACHMENT_ALLOWED_EXT`。
- [ ] **Task 5.2**：灰度验证：先验证上传/下载链路，再放开删除操作。
- [ ] **Task 5.3**：回滚预案：
  - 代码回滚：回退 blueprint 注册与前端入口。
  - 数据回滚：仅在未产生生产附件数据时执行 migration downgrade；否则仅停用入口并保留数据。
- [ ] **Task 5.4**：上线后观测：接口错误率、上传失败率、下载失败率、越权访问告警。

### 风险
- 直接 downgrade 可能导致已上传附件元数据丢失。
- 本地存储路径权限配置错误导致运行时失败。

### 完成定义（DoD）
- 有明确上线检查单、回滚步骤、责任人与触发条件。
- 上线后 24 小时核心指标稳定，无阻塞性缺陷。

---

## 执行顺序摘要（依赖链）
1. **Phase 1 数据库迁移**
2. **Phase 2 后端实现（先契约后实现）**
3. **Phase 3 前端接入（基于稳定 API）**
4. **Phase 4 测试与验收（P0→P1→回归）**
5. **Phase 5 发布与回滚**

> 关键门禁：Phase 2 未通过 API/权限测试，不进入 Phase 3；Phase 4 P0 未全绿，不允许发布。
