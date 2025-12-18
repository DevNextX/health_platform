# 实施计划：健康阈值治理 (Threshold Configuration Governance)

**基于文档**：
- `/docs/requirements/req-threshold-config-governance.md`
- `/docs/epics-and-stories.md`
- `/docs/Design/super-admin-settings-ux.md`

## 1. 概述
本计划旨在实现超级管理员对健康阈值（血压、心率）的全局配置功能。核心目标是允许非代码变更即可调整“健康/异常”判定标准，并实时反映在所有用户的仪表盘中。

**关键约束**：
- 硬性输入安全范围（30-250/30-150）不可变。
- 仅超级管理员可配置。
- MVP 不引入复杂缓存层，直接读取数据库。
- 必须包含审计日志与 CSV 导出。

---

## 2. 阶段划分

| 阶段 | 名称 | 重点 | 预计周期 |
| :--- | :--- | :--- | :--- |
| **Phase 1** | **后端核心与数据模型** | DB Schema, Manager 逻辑, API 基础, 单元测试 | Week 1 (Days 1-3) |
| **Phase 2** | **管理端 UI 开发** | 导航, 配置表单, 预览交互, 发布流程 | Week 1 (Days 4-5) |
| **Phase 3** | **用户端可视化适配** | 仪表盘图表适配, 列表状态标记, 默认值回退 | Week 2 (Days 1-2) |
| **Phase 4** | **审计与验收** | CSV 导出, E2E 测试, 权限边界验证 | Week 2 (Days 3-4) |

---

## 3. 详细任务分解

### Phase 1: 后端核心与数据模型 (Backend Core)

#### 1.1 数据库迁移与模型 (DB Schema)
- [ ] **Task 1.1.1**: 创建 `ThresholdConfig` 模型。
    - 字段：`id`, `systolic_range` (JSON: min, max), `diastolic_range` (JSON), `heart_rate_range` (JSON), `version` (int), `status` (draft/active), `created_at`, `created_by`。
- [ ] **Task 1.1.2**: 创建 `ThresholdAuditLog` 模型。
    - 字段：`id`, `action` (publish/export), `actor_id`, `ip_address`, `user_agent`, `payload_before`, `payload_after`, `timestamp`。
- [ ] **Task 1.1.3**: 生成并运行 Alembic 迁移脚本。
- [ ] **Task 1.1.4**: 实现数据初始化脚本，写入默认阈值 (90-120, 60-90, 60-90) 作为 Version 1。

#### 1.2 业务逻辑层 (Manager Layer)
- [ ] **Task 1.2.1**: 实现 `ThresholdManager.validate_config(payload)`。
    - 校验 Min < Max。
    - 校验必须在硬性安全范围内 (30-250 / 30-150)。
- [ ] **Task 1.2.2**: 实现 `ThresholdManager.create_draft(payload, user)`。
- [ ] **Task 1.2.3**: 实现 `ThresholdManager.publish_config(draft_id, user)`。
    - 事务处理：将当前 Active 标记为 Archived -> 将 Draft 标记为 Active -> 版本号 +1 -> 写入审计日志。
- [ ] **Task 1.2.4**: 实现 `ThresholdManager.get_active_config()`。
- [ ] **Task 1.2.5**: 实现 `ThresholdManager.preview_impact(draft_config)`。
    - 选取最近 50-100 条真实记录，计算在新阈值下的状态分布（正常/异常数量）。

#### 1.3 API 服务层 (Service Layer)
- [ ] **Task 1.3.1**: 定义 Blueprint `super_admin_bp` (路径 `/api/v1/superadmin/`)。
- [ ] **Task 1.3.2**: 实现配置接口：
    - `POST /thresholds/draft` (创建草稿)
    - `GET /thresholds/preview` (预览影响)
    - `POST /thresholds/publish` (发布)
    - `GET /thresholds/active` (获取当前配置 - 公共接口，可能在 `/api/v1/thresholds` 下)
- [ ] **Task 1.3.3**: 添加 RBAC 装饰器 `@require_role('SUPER_ADMIN')` 确保权限安全。

#### 1.4 单元测试
- [ ] **Task 1.4.1**: 测试 `validate_config` 边界条件（如 Min=Max, 超出硬性范围）。
- [ ] **Task 1.4.2**: 测试 `publish_config` 的事务原子性与版本递增。

---

### Phase 2: 管理端 UI 开发 (Frontend Admin)

#### 2.1 导航与路由
- [ ] **Task 2.1.1**: 更新 `src/router/index.js` (或对应路由文件)，添加 `/super-admin/settings` 路由。
- [ ] **Task 2.1.2**: 实现路由守卫：非 SUPER_ADMIN 访问重定向至 Dashboard。
- [ ] **Task 2.1.3**: 更新侧边栏菜单结构，区分 "User Setting" 与 "Super Admin Setting"。

#### 2.2 设置页面开发
- [ ] **Task 2.2.1**: 创建 `SuperAdminSettings` 页面骨架 (Header, Tabs)。
- [ ] **Task 2.2.2**: 开发 `ThresholdForm` 组件。
    - 使用 Ant Design `Form` + `InputNumber`。
    - 实现前端即时校验 (Min < Max)。
- [ ] **Task 2.2.3**: 开发 `PreviewPanel` 组件。
    - 展示 "当前 vs 新设定" 的对比数据（如：异常记录数变化）。
    - 调用 `GET /preview` 接口渲染。

#### 2.3 交互逻辑
- [ ] **Task 2.3.1**: 集成 "保存草稿" 与 "发布" 按钮逻辑。
- [ ] **Task 2.3.2**: 发布成功后的全局提示 (Message/Notification)。

---

### Phase 3: 用户端可视化适配 (User Visualization)

#### 3.1 数据获取
- [ ] **Task 3.1.1**: 在前端 App 初始化或 Dashboard 加载时，调用 `GET /api/v1/thresholds/active` 获取最新阈值。
- [ ] **Task 3.1.2**: 将阈值存入 React Context 或 Redux Store (或简单 State)，供组件消费。

#### 3.2 图表与列表适配
- [ ] **Task 3.2.1**: 修改 `HealthChart.js`。
    - 移除硬编码常量 (`NORMAL_SYSTOLIC_THRESHOLD` 等)。
    - 接收动态阈值 props。
    - 更新 `abnormalMap` 计算逻辑，支持 "临界" (Borderline) 状态（可选，若 MVP 仅需红/绿则保持二元）。
    - 更新 `visualMap` 或 `itemStyle` 颜色逻辑。
- [ ] **Task 3.2.2**: 更新健康记录列表/表格。
    - 根据动态阈值渲染状态标签 (Tag)。

---

### Phase 4: 审计与验收 (Audit & Finalize)

#### 4.1 审计导出
- [ ] **Task 4.1.1**: 实现后端 `GET /api/v1/superadmin/audit/export` 接口。
    - 生成 CSV 流。
    - 包含 BOM 头 (UTF-8)。
    - 文件名符合 RFC5987 (`filename*=UTF-8''...`).
- [ ] **Task 4.1.2**: 在前端 "Super Admin Setting" -> "审计日志" Tab 中添加导出按钮。

#### 4.2 测试与验证
- [ ] **Task 4.2.1**: 编写 E2E 测试 (Playwright)。
    - 场景：Admin 登录 -> 修改阈值 -> 发布 -> 切换 User 账号 -> 验证图表颜色变化。
- [ ] **Task 4.2.2**: 验证安全性：普通 Admin 尝试直接调用 API 应返回 403。

## 4. 依赖检查
- 需确认 `src/security.py` 中是否有现成的 `SUPER_ADMIN` 角色定义与校验装饰器。
- 需确认前端使用的 Ant Design 版本以查阅对应文档。

## 5. 风险管理
- **风险**: 阈值更新后，用户对历史数据的状态变化感到困惑。
- **缓解**: 在仪表盘显著位置添加 Tooltip："基于 2025-12-XX 更新的健康标准"。
