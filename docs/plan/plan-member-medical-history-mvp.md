# Implementation Plan: 家庭成员既往病史管理 MVP

## References
- Requirement: [req-member-medical-history-mvp](../Requirements/req-member-medical-history-mvp.md)
- Design: [design-member-medical-history-mvp](../Design/design-member-medical-history-mvp.md)
- Issue: `#[ID]`（待替换为真实 Issue 编号）

## 目标与交付边界
- 本计划严格执行“前后端一体化交付”：后端 API/数据模型与前端页面/入口必须同时完成。
- 验收必须双线通过：
  - 前端功能验收（页面操作可验证后端能力）。
  - 后端单元测试验收（Pytest 覆盖关键路径并通过）。

## Phase 1: Backend Core（数据模型与服务骨架）

- [ ] **Task 1.1**: 在 `src/models.py` 新增 `MedicalHistory` 模型。
  - 字段：`member_id`、`household_id`、`disease_name`、`onset_date`、`description`、`is_ongoing`、`is_on_medication`、`created_by_user_id`、`updated_by_user_id`、`created_at`、`updated_at`。
  - 时间字段使用 `datetime.now(UTC)`。
- [ ] **Task 1.2**: 生成并提交 Alembic 迁移脚本。
  - 创建 `medical_histories` 表。
  - 建立索引：`(member_id, onset_date)`、`(household_id, member_id)`。
- [ ] **Task 1.3**: 新建 `src/manager/medical_history_manager.py`。
  - 实现 `create/list/get/update/delete`。
  - 统一封装成员归属查询与分页查询。
- [ ] **Task 1.4**: 新建 `src/service/medical_history_service.py`。
  - 暴露 CRUD 接口：`/api/v1/medical-history`。
  - 输入校验：必填、时间格式、布尔字段类型。
  - 归属校验：复用 `MemberManager.get_member(user_id, member_id)`。
- [ ] **Task 1.5**: 在 `src/app.py` 注册 Blueprint。
  - 验证服务成功挂载且不影响现有路由。

### Phase 1 验证
- [ ] 通过接口冒烟：创建/查询/更新/删除各 1 次。
- [ ] 越权访问返回 403/404（按项目错误策略）。

## Phase 2: Backend Quality（单元测试与异常路径）

- [ ] **Task 2.1**: 新增 `tests/test_medical_history.py` 基础 CRUD 测试。
- [ ] **Task 2.2**: 增加参数校验失败测试。
  - 空 `disease_name`。
  - 非法 `onset_date`。
  - 非法布尔值（`is_ongoing`/`is_on_medication`）。
- [ ] **Task 2.3**: 增加权限与隔离测试。
  - 非法 `member_id`。
  - 越权 `member_id`。
  - 成员 A/B 数据隔离。
- [ ] **Task 2.4**: 补充回归测试，确保不破坏既有健康记录接口。

### Phase 2 验证
- [ ] 运行：`python -m pytest tests/test_medical_history.py -v` 通过。
- [ ] 运行：`python -m pytest tests/ -v` 通过（至少与改动相关模块通过）。

## Phase 3: Frontend Core（页面、路由、API 集成）

- [ ] **Task 3.1**: 在 `frontend/src/services/api.js` 新增 `medicalHistoryAPI`。
  - 方法：`list/create/update/delete`。
- [ ] **Task 3.2**: 新建 `frontend/src/pages/MedicalHistory.js`。
  - 列表 + 新增/编辑表单 + 删除操作。
  - 字段完整支持：发病时间、疾病名称、描述、是否仍存在、是否服药。
- [ ] **Task 3.3**: 在 `frontend/src/App.js` 注册 `/medical-history` 路由。
- [ ] **Task 3.4**: 在 `frontend/src/components/Layout.js` 增加“既往病史”菜单入口。
- [ ] **Task 3.5**: 在 `frontend/src/pages/HealthRecords.js` 增加病史入口（跳转独立页面）。
- [ ] **Task 3.6**: 对接 `MemberContext`，确保按当前选中成员筛选病史。
- [ ] **Task 3.7**: 增加 i18n 文案键值（中英），并保持中文文档优先维护。

### Phase 3 验证
- [ ] 前端双入口均可进入病史功能。
- [ ] 新增/编辑/删除后列表实时刷新。
- [ ] 切换成员后病史数据正确隔离。

## Phase 4: E2E & Acceptance（双线验收）

- [ ] **Task 4.1**: 新增/更新 Playwright 场景（`tests/e2e/tests/`）。
  - 登录 -> 成员 A 新增病史 -> 成员 B 不可见 -> 返回成员 A 可见。
  - 从健康记录页入口可跳转并完成新增。
- [ ] **Task 4.2**: 输出前端验收记录（截图或步骤记录）。
- [ ] **Task 4.3**: 输出后端单元测试执行记录（命令与结果）。

### Phase 4 验收清单（必须全部通过）
- [ ] 前端验收通过：双入口、字段完整、成员隔离、错误提示。
- [ ] 后端验收通过：`tests/test_medical_history.py` 与相关回归通过。
- [ ] 任一项未通过则本需求不关闭。

## 风险与应对
- 风险 1：成员归属校验遗漏导致越权。
  - 应对：服务层所有入口统一先做 `MemberManager` 归属校验。
- 风险 2：前后端字段命名不一致导致联调失败。
  - 应对：在 Phase 1 输出 API 示例并在 Phase 3 按契约对齐。
- 风险 3：新增菜单或路由影响现有导航。
  - 应对：补充最小回归测试（健康记录/成员页可正常进入）。

## 完成定义（DoD）
- [ ] 代码已实现前后端完整能力（非单边实现）。
- [ ] 前端手工/自动化验收通过。
- [ ] 后端单元测试通过。
- [ ] 文档已更新（需求、设计、计划一致）。