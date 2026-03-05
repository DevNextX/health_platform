# Design: 家庭成员既往病史管理 MVP

## 1. Overview
- Reference: [需求文档](../requirements/req-member-medical-history-mvp.md)
- Goal: 在现有“成员 + 健康记录”体系上新增“成员级既往病史”能力，满足双入口（健康记录流程入口 + 独立管理页）与前后端一体化实现。
- Non-goal (MVP): 不引入复杂疾病编码体系、不做用药详情管理（仅保留是否服药布尔字段）。

## 1.1 实施范围强约束（Mandatory）
- 本需求必须以前后端一体化方式交付，禁止仅改前端或仅改后端即宣告完成。
- 后端必须提供完整可用 API、数据持久化与权限校验；前端必须提供可操作入口、表单交互与列表展示。
- 验收必须包含两条主线：
  - 前端功能验收（通过页面操作验证后端能力可被真实调用并正确展示）。
  - 后端单元测试验收（Pytest 对核心业务规则与异常路径覆盖通过）。

## 2. Architecture Changes
- **Backend**:
  - 新增病史实体与管理层：`MedicalHistory` + `MedicalHistoryManager`。
  - 新增服务层 Blueprint：`medical_history_bp`，提供成员级 CRUD API。
  - 在 `src/app.py` 注册新路由前缀：`/api/v1/medical-history`。
  - 复用 `MemberManager.get_member(owner_user_id, member_id)` 做成员归属校验，确保只能访问当前用户家庭下的成员数据。
- **Frontend**:
  - 新增独立页面：`frontend/src/pages/MedicalHistory.js`。
  - 在主路由 `frontend/src/App.js` 增加 `medical-history` 路由。
  - 在主菜单 `frontend/src/components/Layout.js` 增加“既往病史”导航项。
  - 在 `HealthRecords` 新增入口（按钮或表单侧边入口），可跳转独立病史页或弹出轻量新增病史表单。
  - 在 `frontend/src/services/api.js` 增加 `medicalHistoryAPI`。

## 3. Data Model
- **Entity**: `MedicalHistory`（新表，建议放在 `src/models.py`）
  - `id`: int, PK
  - `household_id`: int, FK -> `households.id`, not null
  - `member_id`: int, FK -> `members.id`, not null, index
  - `disease_name`: string(120), not null
  - `onset_date`: datetime/date, not null
  - `description`: text, nullable
  - `is_ongoing`: bool, not null, default true
  - `is_on_medication`: bool, not null, default false
  - `created_by_user_id`: int, FK -> `users.id`, not null
  - `updated_by_user_id`: int, FK -> `users.id`, nullable
  - `created_at`: datetime, default `datetime.now(UTC)`, not null
  - `updated_at`: datetime, default `datetime.now(UTC)`, onupdate `datetime.now(UTC)`
- **Index 建议**:
  - `(member_id, onset_date desc)`：支持病史列表主查询。
  - `(household_id, member_id)`：支持权限范围内过滤。
- **删除策略**:
  - MVP 优先使用硬删除（DELETE）；若需审计可后续演进为软删除。
- **Migration**:
  - 新增 Alembic 迁移脚本，创建 `medical_histories` 表与索引。

## 4. API Interface
- **Base Path**: `/api/v1/medical-history`
- **Auth**: 全部 `@jwt_required()`；通过成员归属校验实现数据隔离。

- `GET /api/v1/medical-history?member_id={id}&page={page}&size={size}`
  - Purpose: 获取成员病史列表（分页）。
  - Validation:
    - `member_id` 必填且必须属于当前用户家庭。
    - 分页参数遵循项目规范：`page` + `size`。
  - Response:
    - `{ histories: [...], pagination: {...} }`

- `POST /api/v1/medical-history`
  - Request Body:
    - `member_id` (required)
    - `disease_name` (required)
    - `onset_date` (required, ISO string)
    - `description` (optional)
    - `is_ongoing` (required, boolean)
    - `is_on_medication` (required, boolean)
  - Validation:
    - 必填字段不能为空。
    - `onset_date` 格式合法。
    - `member_id` 归属合法。
  - Response: 创建后的病史对象。

- `PUT /api/v1/medical-history/{history_id}`
  - Purpose: 更新病史条目。
  - Validation:
    - `history_id` 存在且属于当前用户可访问成员。
    - 入参字段按白名单更新。
  - Response: 更新后的病史对象。

- `DELETE /api/v1/medical-history/{history_id}`
  - Purpose: 删除病史条目。
  - Validation:
    - `history_id` 存在且权限合法。
  - Response: `{ message: "Deleted" }`

- `GET /api/v1/medical-history/summary?member_id={id}`（可选）
  - Purpose: 健康记录页快速展示“当前进行中病史摘要”。
  - MVP 可选实现：若不实现单独接口，可由列表接口前端筛选 `is_ongoing=true`。

## 5. Component Design
- **Backend Components**:
  - `src/models.py`: 新增 `MedicalHistory` 模型。
  - `src/manager/medical_history_manager.py`: CRUD、分页查询、归属约束查询。
  - `src/service/medical_history_service.py`: 输入校验、HTTP 状态码、错误结构。
  - `src/app.py`: Blueprint 注册。
- **Frontend Components**:
  - `frontend/src/pages/MedicalHistory.js`: 独立病史管理页（列表 + 新增/编辑弹窗）。
  - `frontend/src/pages/HealthRecords.js`: 增加病史入口（跳转/弹窗二选一，MVP 建议“跳转独立页”降低耦合）。
  - `frontend/src/services/api.js`: 新增 `medicalHistoryAPI`。
  - `frontend/src/components/Layout.js`: 菜单新增“既往病史”。
  - `frontend/src/i18n/*`: 补充菜单、字段、状态文案键值。

## 6. Validation & Security Design
- 成员归属校验：
  - 所有病史读写均先通过 `MemberManager.get_member(user_id, member_id)` 验证成员归属。
- 字段校验：
  - `disease_name`: 非空，长度限制（建议 1-120）。
  - `onset_date`: ISO 时间格式，后端统一为 UTC 存储。
  - `is_ongoing` / `is_on_medication`: 严格 boolean。
- 敏感数据处理：
  - 不跨家庭返回数据；错误信息避免泄露他人资源存在性细节。

## 7. Testing Strategy
- **Backend (Pytest)**
  - 新增 `tests/test_medical_history.py`：
    - 创建/列表/更新/删除。
    - 非法 member_id、越权 member_id。
    - 必填字段与时间格式校验。
    - 成员切换后的数据隔离。
- **Frontend**
  - 页面基本交互测试（至少验证新增与列表刷新）。
- **E2E (Playwright)**
  - 用户登录 -> 选择成员 A 新增病史 -> 切换成员 B 不可见 -> 回到成员 A 可见。
  - 从健康记录页入口可进入病史功能。

## 8. Rollout & Compatibility
- 该功能为增量扩展，不影响现有 `health_records` 表结构。
- 与现有成员选择上下文 `MemberContext` 兼容，通过 `selectedMemberId` 作为默认查询成员。
- 旧用户无病史数据时返回空列表，不阻断现有流程。

## 9. High-Level Task Blocks
- [ ] Database Migration
  - [ ] Add `MedicalHistory` model and migration script
  - [ ] Add indexes for member-level query paths
- [ ] Backend Service Logic
  - [ ] Implement `MedicalHistoryManager`
  - [ ] Implement service endpoints and payload validation
  - [ ] Register blueprint in app factory
- [ ] Frontend Integration
  - [ ] Add `medicalHistoryAPI`
  - [ ] Add `MedicalHistory` page and route
  - [ ] Add entry from `HealthRecords` and menu item in `Layout`
  - [ ] Add i18n keys (zh/en)
- [ ] Testing & Verification
  - [ ] Add backend unit tests
  - [ ] Add/Update Playwright scenario for member isolation and dual entry

## 10. 验收口径（Definition of Done）

### 10.1 前端验收（必须通过）
- [ ] 可从两个入口访问病史能力：
  - 健康记录页入口。
  - 独立“既往病史”页面入口。
- [ ] 在前端新增病史时，字段完整可输入并提交成功：发病时间、疾病名称、描述、是否仍存在、是否服药。
- [ ] 前端编辑/删除病史后，列表即时刷新且状态正确。
- [ ] 切换家庭成员后，页面仅显示当前成员病史，数据不串成员。
- [ ] 前端对必填和时间格式给出可见错误提示，且不发送无效提交。

### 10.2 后端单元测试验收（必须通过）
- [ ] 新增 `tests/test_medical_history.py`，并覆盖：
  - CRUD 正常路径。
  - 参数校验失败路径（必填缺失、时间格式错误、布尔字段非法）。
  - 权限与归属校验（越权 member_id、无效 history_id）。
  - 成员隔离（成员 A 数据不可被成员 B 查询/修改）。
- [ ] 运行后端测试命令通过：`python -m pytest tests/ -v`（至少新增模块与相关回归通过）。

### 10.3 综合通过标准
- [ ] 前端验收清单全部通过。
- [ ] 后端单元测试清单全部通过。
- [ ] 两条验收主线任一未通过，则本需求不视为完成。