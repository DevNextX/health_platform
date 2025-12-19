# DevOps Agent Workflow Guide

**快速指南：如何使用 AI Agent 完成功能开发全流程**

---

## 🎯 核心概念

本项目定义了 **4 个专业化 AI Agent**，覆盖从需求到实现的完整生命周期：

```
1. DevOps_Product_Manager     → 需求分析 ("做什么？为什么？")
2. DevOps_System_Architect    → 技术设计 ("如何架构？")
3. DevOps_Tech_Lead_Planner   → 任务分解 ("分几步？谁先谁后？")
4. Developer                  → 代码实现 ("具体怎么写？")
```

**特色功能**：
- ✅ 自动生成规范化文档（需求、设计、计划）
- ✅ 自动创建 GitHub Issue + Sub-tasks
- ✅ 自动触发 Handoff（角色间无缝衔接）

---

## 📋 标准工作流（完整功能）

### Step 1: 需求分析 (Product_Manager)

**触发方式**：
```markdown
@DevOps_Product_Manager 用户希望超级管理员可以配置健康判定阈值
```

**Agent 操作**：
1. 通过对话澄清需求细节
2. 识别边界场景与约束
3. 生成需求文档：`/docs/requirements/req-[slug].md`
4. 创建 GitHub Issue（标签：`feature`, `planning`）
5. 触发 Handoff → `DevOps_System_Architect`

**输出示例**：
```markdown
## 验收标准 (AC)
- [ ] AC1: 超级管理员可在 UI 配置血压/心率阈值
- [ ] AC2: 配置后立即生效于仪表盘
- [ ] AC3: 每次变更记录审计日志

## 边界场景
- 输入冲突: 尝试设置 Min > Max，前端应阻止提交
```

---

### Step 2: 技术设计 (System_Architect)

**触发方式**（自动或手动）：
```markdown
@DevOps_System_Architect /docs/requirements/req-threshold-config.md
```

**Agent 操作**：
1. 阅读需求文档 + 分析现有代码
2. 设计 4 个维度：
   - 数据模型（Schema, 字段, 约束）
   - API 合约（端点, 请求/响应, 鉴权）
   - 组件架构（前端组件树, 状态管理）
   - 集成流程（序列图, 数据流）
3. 生成设计文档：`/docs/design/design-[slug].md`
4. 更新 GitHub Issue（添加设计链接）
5. 触发 Handoff → `DevOps_Tech_Lead_Planner`

**输出示例**：
```markdown
## 数据模型
Entity: ThresholdConfig
- id: int (PK)
- systolic_range: JSON {"min": 90, "max": 120}
- status: enum (draft, active, archived)

## API 设计
POST /api/v1/superadmin/thresholds
- Auth: @require_role('SUPER_ADMIN')
- Request: {systolic: {min, max}, diastolic: {...}}
- Response: {id, version, status}
```

---

### Step 3: 任务分解 (Tech_Lead_Planner)

**触发方式**（自动或手动）：
```markdown
@DevOps_Tech_Lead_Planner /docs/design/design-threshold-config.md
```

**Agent 操作**：
1. 阅读设计文档
2. 按层级分解任务：
   - **Phase 1**: Database & Models
   - **Phase 2**: Backend Logic & API
   - **Phase 3**: Frontend Components
   - **Phase 4**: Testing & Verification
3. 生成实施计划：`/docs/plan/plan-[slug].md`
4. **自动创建 GitHub Sub-issues**：
   - 为每个 Phase 创建一个 Sub-task Issue
   - 主 Issue 更新为 Checklist（`- [ ] #102 Phase 1: ...`）
   - 在主 Issue 发布计划摘要评论
5. 触发 Handoff → `Developer`

**输出示例**：
```markdown
## Phase 1: Database & Models
- [ ] Task 1.1: 在 src/models.py 添加 ThresholdConfig 类
      - 字段: id, systolic_range (JSON), status (Enum)
      - 验证: 模型可导入无错误
      
- [ ] Task 1.2: 生成迁移脚本
      - 命令: flask db migrate -m "add threshold config"
      - 验证: 迁移文件生成在 migrations/versions/

## Phase 2: Backend Logic & API
- [ ] Task 2.1: 创建 src/manager/threshold_manager.py
      - 实现: get_active(), validate_config(), publish()
      - 验证: 单元测试通过 tests/test_threshold_manager.py
```

**GitHub Issue 结构**：
```
Issue #101 (主 Issue)
├── Sub-issue #102: [Phase 1] Database - Add ThresholdConfig Model
├── Sub-issue #103: [Phase 2] Backend - Implement Threshold Manager
├── Sub-issue #104: [Phase 3] Frontend - Build Config Form
└── Sub-issue #105: [Phase 4] Testing - E2E Verification
```

---

### Step 4: 代码实现 (Developer)

**触发方式**（自动或手动）：
```markdown
@Developer /docs/plan/plan-threshold-config.md
或
@Developer "请开始实现 Issue #102: Database setup"
```

**开发者操作**：
1. 按照 Plan 中的 Task 顺序实现
2. 每完成一个 Phase，提交代码：
   ```bash
   git commit -m "feat(threshold): add config model (ref #102)"
   ```
3. 创建 PR，关联 Sub-issue：
   ```markdown
   Closes #102
   ```
4. 合并后，GitHub 自动关闭 Sub-issue，主 Issue Checklist 自动勾选

---

## 🚀 快速命令参考

### 完整流程（一键启动）
```markdown
@DevOps_Product_Manager [功能描述]
# 后续 Agent 会自动 Handoff
```

### 跳过需求阶段（已有明确需求）
```markdown
@DevOps_System_Architect "基于现有需求 /docs/requirements/req-xxx.md 设计技术方案"
```

### 仅需任务分解（已有设计）
```markdown
@DevOps_Tech_Lead_Planner /docs/design/design-xxx.md
```

### 仅需代码实现（已有计划）
```markdown
@Developer /docs/plan/plan-xxx.md
```

---

## 📊 文件输出结构

```
docs/
├── requirements/           # Product_Manager 输出
│   └── req-threshold-config.md
├── design/                 # System_Architect 输出
│   └── design-threshold-config.md
└── plan/                   # Tech_Lead_Planner 输出
    └── plan-threshold-config.md

GitHub Issues
├── Issue #101: [Feature] Threshold Configuration
│   ├── Sub-issue #102: [Phase 1] Database
│   ├── Sub-issue #103: [Phase 2] Backend
│   ├── Sub-issue #104: [Phase 3] Frontend
│   └── Sub-issue #105: [Phase 4] Testing
```

---

## ✅ 最佳实践

### 1. 遵循流程顺序
- ✅ **推荐**: Product_Manager → Architect → Planner → Developer
- ❌ **避免**: 直接让 Architect 分解任务（越过 Planner）

### 2. 利用 Handoff 机制
- ✅ 让 Agent 自动触发下一个 Agent
- ❌ 手动复制粘贴文档路径

### 3. 关联 GitHub Issue
- ✅ 提交信息引用 Issue: `feat(xxx): ... (ref #102)`
- ✅ PR 描述使用: `Closes #102`
- ❌ 忘记关联，导致无法追溯

### 4. 保持文档同步
- ✅ 需求变更时，重新运行 Product_Manager
- ❌ 直接修改 Plan 文档，跳过设计阶段

---

## 🔧 故障排查

### Q: Handoff 没有自动触发？
**A**: 检查 Agent 配置中的 `handoffs` 字段是否正确设置目标 Agent。

### Q: GitHub Issue 没有创建？
**A**: 确认 Tech_Lead_Planner 有 `github/*` 工具权限，且工作区已连接 GitHub。

### Q: Sub-issue 没有关联到主 Issue？
**A**: 检查 Sub-issue Body 中是否包含 `Related to #[MAIN_ID]`，主 Issue 是否有 Checklist。

---

## 📚 相关文档

- [AGENT_ROLE_OPTIMIZATION.md](./AGENT_ROLE_OPTIMIZATION.md) - 角色优化详解
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 代码提交规范
- [.github/prompts/sync-issue.prompt.md](../.github/prompts/sync-issue.prompt.md) - Issue 同步模板

---

**维护状态**: ✅ 活跃  
**最后更新**: 2025-12-19  
**适用版本**: Health Platform v1.5+
