# Agent Role Optimization Summary

**Date**: 2025-12-19  
**Objective**: Eliminate role duplication and clarify responsibilities

## 🎯 优化结果

### 整合后的三阶段工作流

```
Product_Manager → System_Architect → Tech_Lead_Planner → Developer
  (需求分析)      (技术设计)         (任务分解)          (代码实现)
```

---

## 📋 优化前后对比

| Agent名称 | 优化前问题 | 优化后职责 | 输出 |
|----------|-----------|----------|------|
| **DevOps-PM2.agent.md** | 与Product_Manager重复 | ✅ **统一为Product_Manager**<br/>需求分析，澄清"做什么 & 为什么" | `/docs/requirements/req-*.md` |
| **DevOops_Plan.agent.md** | 与Tech_Lead_Planner重复，输出过于简单 | ✅ **增强为Tech_Lead_Planner**<br/>按层级分解任务（DB→Backend→Frontend→Testing） | `/docs/plan/plan-*.md` |
| **DevOps_Architecture.agent.md** | ADR ≠ 设计文档，职责错位 | ✅ **改为System_Architect**<br/>技术设计（数据模型、API、组件、集成） | `/docs/design/design-*.md` |

---

## 🔧 详细优化内容

### 1. Product_Manager (原DevOps-PM2)

**核心职责**：需求精炼 - 澄清业务价值与范围

**关键改进**：
- ✅ 更新工具列表为现代命名
- ✅ 明确handoff目标：System_Architect
- ✅ 强调"What & Why"，禁止谈论"How"
- ✅ 与GitHub Issue强绑定

**工作流**：
```
1. 对话澄清 → 识别边界场景
2. 生成需求草稿 → 等待确认
3. 保存 /docs/requirements/ → 同步到GitHub Issue
4. 触发 handoff 到 System_Architect
```

**输出模板**：
- 背景 & 价值
- 范围 & 边界
- 验收标准（AC）
- 边界场景
- 约束 & 非功能需求
- 风险/问题
- 测试提示

---

### 2. System_Architect (原DevOps_Architecture)

**核心职责**：技术设计 - 定义系统如何构建

**关键改进**：
- ✅ 从"ADR记录者"改为"设计者"
- ✅ 覆盖4个维度：数据模型、API、组件、集成
- ✅ 包含风险分析和非功能需求
- ✅ 输出适配Planner需求

**设计维度**：
1. **数据模型设计**：表结构、字段、约束、关系
2. **API合约设计**：端点、请求/响应Schema、状态码
3. **组件架构**：前端组件层级、状态管理、Hooks
4. **集成 & 数据流**：序列图、转换逻辑

**输出文档结构**：
```markdown
# Technical Design: [Title]

## 1. Overview
## 2. Data Model (详细Schema)
## 3. API Design (完整接口规范)
## 4. Frontend Architecture (组件树+状态)
## 5. Integration & Data Flow (序列图)
## 6. Non-Functional Requirements
## 7. Risk Analysis
## 8. High-Level Task Summary (供Planner展开)
```

---

### 3. Tech_Lead_Planner (原DevOops_Plan)

**核心职责**：任务分解 - 将设计拆解为可执行单元

**关键改进**：
- ✅ 从"3-6步简化计划"改为"按层级详细分解"
- ✅ 明确分层顺序：Database → Backend → Frontend → Testing
- ✅ 每个任务包含：文件路径、具体操作、验证步骤
- ✅ 任务粒度：< 2小时可完成

**分层结构**：
```markdown
## Phase 1: Database & Models
- Task 1.1: 更新 src/models.py
- Task 1.2: 生成迁移脚本
- Task 1.3: 运行迁移并验证

## Phase 2: Backend Logic & API
- Task 2.1: 实现 Manager 层 (src/manager/)
- Task 2.2: 实现 Service 层 (src/service/)
- Task 2.3: 添加单元测试 (tests/)

## Phase 3: Frontend Components
- Task 3.1: 创建React组件 (frontend/src/)
- Task 3.2: 集成后端API
- Task 3.3: 添加i18n翻译

## Phase 4: Testing & Verification
- Task 4.1: 运行后端单元测试
- Task 4.2: 添加E2E测试
- Task 4.3: 手动验证清单
```

**任务质量标准**：
- ✅ 明确文件路径和函数名
- ✅ 包含验证步骤
- ✅ 不跨层（避免"同时改DB和UI"）
- ✅ 可追溯（引用需求和设计文档）

---

## 🎭 角色边界清晰化

| 角色 | 回答的问题 | 禁止涉及的内容 | 交付物 |
|------|----------|---------------|-------|
| **Product_Manager** | 做什么？为什么？ | ❌ 数据库Schema<br/>❌ API端点<br/>❌ 组件名称 | 需求文档 |
| **System_Architect** | 怎么设计？用什么技术？ | ❌ 具体代码实现<br/>❌ 实施步骤顺序 | 设计文档 |
| **Tech_Lead_Planner** | 分几步？谁先谁后？ | ❌ 编写代码<br/>❌ 执行迁移 | 实施计划 |
| **Developer** | 如何编码？测试是否通过？ | ❌ 修改需求<br/>❌ 改变设计 | 代码 + 测试 |

---

## 🔗 协作流程示例

### 场景：新增"健康阈值配置"功能

#### Step 1: Product_Manager
**输入**：用户提出"希望超级管理员可以配置健康判定标准"
**输出**：`/docs/requirements/req-threshold-config.md`
```markdown
## 验收标准
- [ ] AC1: 超级管理员可在UI配置血压/心率阈值
- [ ] AC2: 配置后立即生效于仪表盘
- [ ] AC3: 记录审计日志
```
**Handoff**: → System_Architect

---

#### Step 2: System_Architect
**输入**：`req-threshold-config.md` + 现有代码分析
**输出**：`/docs/design/design-threshold-config.md`
```markdown
## 数据模型
Entity: ThresholdConfig
- systolic_min: int (30-250)
- systolic_max: int (30-250)
- status: enum (draft, active, archived)

## API设计
POST /api/v1/superadmin/thresholds
- Auth: SUPER_ADMIN
- Request: {systolic: {min, max}, ...}

## 组件架构
ThresholdForm (Ant Design Form)
└── RangeInputGroup (InputNumber x2)
```
**Handoff**: → Tech_Lead_Planner

---

#### Step 3: Tech_Lead_Planner
**输入**：`design-threshold-config.md`
**输出**：`/docs/plan/plan-threshold-config.md`
```markdown
## Phase 1: Database & Models
- [ ] Task 1.1: 在 src/models.py 添加 ThresholdConfig 类
      验证: 模型可导入无错误
- [ ] Task 1.2: 生成迁移: flask db migrate -m "add threshold config"
      验证: 迁移文件生成在 migrations/versions/

## Phase 2: Backend Logic
- [ ] Task 2.1: 创建 src/manager/threshold_manager.py
      实现: get_active(), validate_config(), publish()
      验证: 单元测试通过 tests/test_threshold_manager.py
```
**Handoff**: → Developer

---

#### Step 4: Developer
**输入**：`plan-threshold-config.md`
**操作**：
1. 编码：实现 Task 1.1, 1.2, 2.1 等
2. 测试：运行 `pytest -v`
3. 提交：`feat(threshold): add config management`

---

## 📊 文件组织结构

```
docs/
├── requirements/           # Product_Manager输出
│   ├── req-threshold-config.md
│   └── req-tag-filter.md
├── design/                 # System_Architect输出
│   ├── design-threshold-config.md
│   └── design-tag-filter.md
└── plan/                   # Tech_Lead_Planner输出
    ├── plan-threshold-config.md
    └── plan-tag-filter.md
```

---

## ✅ 优化收益

### 1. 清晰的职责边界
- ❌ 消除重复：不再有2个PM、2个Planner
- ✅ 单一职责：每个Agent专注一件事

### 2. 完整的工作流
- ✅ 需求 → 设计 → 计划 → 实现
- ✅ 每个阶段有明确输入/输出
- ✅ Handoff机制自动传递

### 3. 可追溯性
- ✅ 每个文档引用前序文档
- ✅ 所有内容同步到GitHub Issue
- ✅ 便于Code Review和QA验证

### 4. 适应复杂项目
- ✅ Architect输出足够详细（非简化版）
- ✅ Planner按层级分解（非3-6步笼统）
- ✅ 支持多层架构（DB/Backend/Frontend/Testing）

---

## 🚀 使用建议

### 标准流程（完整功能）
```bash
# 1. 需求分析
@Product_Manager "用户希望管理员可以配置健康阈值"

# 2. 技术设计（自动触发或手动）
@System_Architect "/docs/requirements/req-threshold-config.md"

# 3. 任务分解（自动触发或手动）
@Tech_Lead_Planner "/docs/design/design-threshold-config.md"

# 4. 编码实现
@Developer "/docs/plan/plan-threshold-config.md"
```

### 快速迭代（仅部分阶段）
```bash
# 仅需计划分解
@Tech_Lead_Planner "基于现有设计，分解数据库迁移任务"

# 仅需设计审查
@System_Architect "评审当前API设计是否符合RESTful"
```

---

## � GitHub Issue 集成增强 (NEW)

### 增强背景
为提高全流程可追溯性，**Tech_Lead_Planner** 现在在生成实施计划后，自动执行 GitHub Issue 管理操作。

### 新增能力

#### 1. 主 Issue 创建或关联
- **检查逻辑**：搜索是否存在与功能相关的 Issue
- **创建条件**：若不存在，则创建主 Issue
  - **标题格式**：`[Feature] [需求标题]`
  - **内容结构**：
    ```markdown
    ## Background
    [从需求文档提取]
    
    ## Documents
    - Requirement: /docs/requirements/req-[slug].md
    - Design: /docs/design/design-[slug].md
    - Plan: /docs/plan/plan-[slug].md
    
    ## High-Level Scope
    [概述功能范围]
    ```
  - **标签**: `feature`, `planning`

#### 2. 子任务 Issue 自动分解
每个 Phase 对应一个子任务 Issue：

| Phase | Sub-Issue 标题示例 | 标签 |
|-------|------------------|------|
| **Phase 1** | `[Phase 1] Database - Add ThresholdConfig Model` | `sub-task`, `database` |
| **Phase 2** | `[Phase 2] Backend - Implement Threshold Manager API` | `sub-task`, `backend` |
| **Phase 3** | `[Phase 3] Frontend - Build Threshold Config Form` | `sub-task`, `frontend` |
| **Phase 4** | `[Phase 4] Testing - Add E2E Verification` | `sub-task`, `testing` |

**子任务内容模板**：
```markdown
## Parent Issue
Related to #[MAIN_ISSUE_ID]

## Objective
[1-2 sentence description from plan]

## Tasks
- [ ] Task X.1: [Description + file path]
- [ ] Task X.2: [Description + verification]

## Files Involved
- `src/models.py`
- `src/manager/threshold_manager.py`

## Verification
- [ ] Unit tests pass
- [ ] No linting errors
- [ ] Manual verification completed

## References
- [Implementation Plan](../../docs/plan/plan-[slug].md#phase-x)
- [Design Doc](../../docs/design/design-[slug].md)
```

#### 3. 主 Issue 关联清单
Tech_Lead_Planner 会更新主 Issue，添加子任务 Checklist：
```markdown
## Implementation Phases
- [ ] #102 Phase 1: Database & Models
- [ ] #103 Phase 2: Backend Logic & API
- [ ] #104 Phase 3: Frontend Components
- [ ] #105 Phase 4: Testing & Verification
```

#### 4. 完整性保障
- ✅ 计划文档保存至 `/docs/plan/plan-[slug].md`
- ✅ 将计划摘要作为评论发布到主 Issue
- ✅ 输出所有 Issue URL 供用户验证
- ✅ 触发 Developer Handoff（携带 Issue ID）

---

### 更新后的工作流

```
Product_Manager (需求) → 创建 Issue #101
    ↓                     标签: feature, planning
System_Architect (设计) → 更新 Issue #101 (添加设计链接)
    ↓
Tech_Lead_Planner (计划) → 创建 Sub-issues #102-#105
    ↓                      主 Issue 更新为 Checklist
    ↓                      发布计划摘要评论
Developer (实现)        → 关联到 Sub-issue (#102...)
    ↓                      提交 PR 引用 Issue: "Closes #102"
    ↓
完成合并后              → GitHub 自动关闭 Sub-issue
                         主 Issue Checklist 自动勾选
```

---

### 协作流程示例（含 GitHub Issue）

#### Step 1: Product_Manager
**输出**：`/docs/requirements/req-threshold-config.md` + **创建 Issue #101**

#### Step 2: System_Architect
**输出**：`/docs/design/design-threshold-config.md` + **更新 Issue #101** (添加设计链接)

#### Step 3: Tech_Lead_Planner
**输出**：`/docs/plan/plan-threshold-config.md` + **执行以下操作**：
1. 创建 Sub-issue #102: `[Phase 1] Database - Add ThresholdConfig Model`
2. 创建 Sub-issue #103: `[Phase 2] Backend - Implement Threshold Manager`
3. 创建 Sub-issue #104: `[Phase 3] Frontend - Build Config Form`
4. 创建 Sub-issue #105: `[Phase 4] Testing - E2E Verification`
5. 更新 Issue #101 Body：添加 Checklist
6. 在 Issue #101 发布评论：计划摘要 + 链接

**Handoff**: → Developer（"Please start with Issue #102: Database setup"）

#### Step 4: Developer
**操作**：
1. 从 Sub-issue #102 开始实现
2. 提交代码：`feat(threshold): add config model (ref #102)`
3. 创建 PR：`Closes #102` → 合并后自动关闭
4. Issue #101 的 Checklist 自动勾选

---

### GitHub Issue 集成优势

| 优势 | 说明 |
|------|-----|
| ✅ **全流程可追溯** | 从需求讨论 → 设计变更 → 任务分解 → 代码实现，全部关联 |
| ✅ **任务粒度清晰** | Phase 级别拆分，每个 Sub-issue 独立可验证 |
| ✅ **进度可视化** | 通过 Checklist + GitHub Projects 看板实时跟踪 |
| ✅ **代码变更可关联** | PR 引用 Issue ID，方便 Code Review 和回溯 |
| ✅ **自动化程度高** | 合并 PR 自动关闭 Issue，减少手动维护 |

---

### 参考资料
- `.github/prompts/sync-issue.prompt.md` - Issue 创建与同步模式
- GitHub REST API - Issues & Sub-issues 管理

---

## 📝 后续优化空间

1. **ADR Agent分离**：如需记录架构决策（选型、模式），可独立创建ADR Agent
2. **QA Agent补充**：测试策略规划、用例设计可由专门QA Agent负责
3. **文档模板自动化**：基于Agent输出自动生成Swagger、Changelog
4. **GitHub Projects 集成**：自动将 Sub-issues 添加到看板（Backlog/In Progress/Done）

---

**Status**: ✅ 优化完成 + GitHub Issue集成增强  
**影响文件**: 3个Agent配置文件 (DevOps_Product_Manager, DevOps_System_Architect, DevOps_Tech_Lead_Planner)  
**兼容性**: 与现有role-*系列Agent无冲突  
**新增能力**: 自动化 Issue/Sub-issue 创建与关联
