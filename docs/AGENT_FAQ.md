# 关于 Agent 执行模式的问题解答

**Date**: 2025-12-19  
**针对问题**: Agent 自动触发 & Context 模式

---

## ❓ 问题 1: @DevOps_Product_Manager 会自动触发后续 agent 吗？

### 短答案
**不会自动触发**。需要用户手动点击 "Proceed to Design" 按钮。

### 详细说明

**当前机制（Handoffs）**：
```markdown
@DevOps_Product_Manager 用户希望超级管理员可以配置健康阈值

执行流程：
1. Product_Manager 完成需求分析
2. 生成 /docs/requirements/req-xxx.md
3. 创建 GitHub Issue #101
4. 显示 "Proceed to Design" 按钮 ← 需要用户点击
5. (新 chat session) 手动触发 System_Architect
```

**Handoffs 字段的作用**：
- ✅ 提供"下一步建议"
- ✅ 预填充目标 agent 和 prompt
- ❌ **不会自动执行**后续 agent

---

## ❓ 问题 2: 每个 agent 运行在各自的 context 还是同一个 context？

### 短答案
**默认是各自独立 context**（新 chat session）。

### 两种模式对比

#### 模式 A: Handoffs（独立 Context）
```
Chat Session 1: @DevOps_Product_Manager
  - Context: 用户输入
  - Output: req.md, Issue #101
  - Memory: 仅此 chat 可见
  ↓ (点击按钮)
  
Chat Session 2: @DevOps_System_Architect /docs/requirements/req-xxx.md
  - Context: 仅文件路径（无 Chat 1 历史）
  - Output: design.md
  - Memory: 无法访问 Chat 1
  ↓ (点击按钮)
  
Chat Session 3: @DevOps_Tech_Lead_Planner /docs/design/design-xxx.md
  - Context: 仅文件路径（无前序历史）
  - Output: plan.md, Sub-issues
  - Memory: 无法访问 Chat 1/2
```

**特点**：
- ✅ 每个 agent 独立运行
- ❌ 无法访问前序对话
- ❌ 仅通过文件路径传递信息

---

#### 模式 B: Subagents（结果汇总到主 Session）⭐
```
Chat Session 1 (Main): Execute full workflow for: [Feature]
  ├── runSubagent(DevOps_Product_Manager)
  │   - Context: 独立 context window（隔离）
  │   - Process: 分析需求、创建文档
  │   - Return: req.md 路径, Issue #101 → 汇总到主 session
  │
  ├── Main Session 接收 PM 结果
  │   └── 将结果传递给下一个 subagent
  │
  ├── runSubagent(DevOps_System_Architect)
  │   - Context: 独立 context window（隔离）
  │   - Input: 从主 session 获取 req 路径
  │   - Process: 读取文件、创建设计
  │   - Return: design.md 路径 → 汇总到主 session
  │
  ├── Main Session 接收 Architect 结果
  │   └── 将结果传递给下一个 subagent
  │
  └── runSubagent(DevOps_Tech_Lead_Planner)
      - Context: 独立 context window（隔离）
      - Input: 从主 session 获取 req + design 路径
      - Process: 读取文件、创建计划、创建 Issues
      - Return: plan.md 路径, Sub-issue IDs → 汇总到主 session
```

**特点**：
- ✅ 所有结果汇总到同一 main chat session
- ✅ 主 session 协调并传递结果给下一个 subagent
- ⚠️ 每个 subagent 有**独立 context**（不直接访问其他 subagent）
- ✅ 统一的对话历史（主 session）

---

## ❓ 问题 3: 如何使用 Subagent 模式？

### 是的，需要明确说明使用 runSubagent

**正确用法**：

```markdown
Execute the full feature development workflow for: Super Admin can configure health thresholds

Use runSubagent to sequentially invoke:
1. DevOps_Product_Manager - Requirements analysis + GitHub Issue creation
2. DevOps_System_Architect - Technical design + Issue update
3. DevOps_Tech_Lead_Planner - Implementation plan + Sub-issues creation

After each step, capture outputs (file paths, Issue IDs) and pass to next agent.
Generate a final summary with all document links and Issue URLs.
```

**关键词**：
- ✅ `Use runSubagent`
- ✅ `sequentially invoke`
- ✅ `capture outputs`
- ✅ `pass to next agent`

---

## 📋 推荐用法模板

### 模板 1: 完整工作流（Subagent 模式）

```markdown
Execute the full feature development workflow for: [YOUR_FEATURE_DESCRIPTION]

Use runSubagent to sequentially invoke:
1. DevOps_Product_Manager - Requirements analysis + GitHub Issue creation
2. DevOps_System_Architect - Technical design + Issue update
3. DevOps_Tech_Lead_Planner - Implementation plan + Sub-issues creation

After each step, capture outputs and pass to next agent.
Generate final summary with all links.
```

**示例**：
```markdown
Execute the full feature development workflow for: Add role-based dashboard customization. Users with different roles should see different widgets and default views.

Use runSubagent to sequentially invoke:
1. DevOps_Product_Manager - Requirements analysis + GitHub Issue creation
2. DevOps_System_Architect - Technical design + Issue update  
3. DevOps_Tech_Lead_Planner - Implementation plan + Sub-issues creation

After each step, capture outputs and pass to next agent.
Generate final summary with all links.
```

---

### 模板 2: 跳过需求阶段（已有文档）

```markdown
Based on existing requirement document at /docs/requirements/req-[slug].md, execute design and planning workflow.

Use runSubagent to sequentially invoke:
1. DevOps_System_Architect - Read requirement, create technical design
2. DevOps_Tech_Lead_Planner - Read design, create implementation plan + Sub-issues

Capture outputs and generate summary.
```

---

### 模板 3: 仅规划阶段（设计已完成）

```markdown
Based on requirement at /docs/requirements/req-[slug].md and design at /docs/design/design-[slug].md, execute planning workflow.

Use runSubagent DevOps_Tech_Lead_Planner to:
1. Read requirement and design documents
2. Create detailed implementation plan
3. Create GitHub Sub-task Issues for each phase
4. Update main Issue with checklist

Generate summary with all Issue URLs.
```

---

## 📊 决策矩阵：选择哪种模式？

| 场景 | 推荐模式 | 原因 |
|-----|---------|------|
| 功能需求明确，无需反复讨论 | **Subagent** | 一次性完成，快速 |
| 需求需要多轮澄清 | **Handoffs** | 可暂停和修正 |
| 时间紧迫，需要快速交付 | **Subagent** | 自动化程度高 |
| 团队学习新流程 | **Handoffs** | 每步可观察和学习 |
| 需要统一审计追踪 | **Subagent** | 单一对话历史 |
| 设计需要外部审批 | **Handoffs** | 可在审批期间暂停 |
| 批量处理多个类似功能 | **Subagent** | 自动化执行 |

---

## ✅ 总结

### 回答您的问题：

1. **@DevOps_Product_Manager 会自动触发后续 agent 吗？**
   - ❌ **不会**。Handoffs 机制需要用户手动点击按钮。
   - ✅ 要实现自动触发，需使用 **Subagent 模式**。

2. **每个 agent 运行在各自 context 还是同一 context？**
   - **Handoffs 模式**：各自独立 context（新 chat session）
   - **Subagent 模式**：每个 subagent 有独立 context，但**结果汇总到主 session**

3. **如何使用 Subagent 模式？**
   - ✅ 需在 prompt 中**明确说明**使用 `runSubagent`
   - ✅ 使用我们提供的模板（见上方）
   - ✅ 参考 `.github/prompts/feature-workflow.prompt.md`
   - ⚠️ **重要**：Subagents 有独立 context，需主 session 传递参数（文件路径、Issue ID）

---

## 📚 参考文档

- **[AGENT_EXECUTION_MODELS.md](./AGENT_EXECUTION_MODELS.md)** - 两种模式详细对比
- **[.github/prompts/feature-workflow.prompt.md](../.github/prompts/feature-workflow.prompt.md)** - Subagent 工作流模板
- **[DEVOPS_AGENT_WORKFLOW_GUIDE.md](./DEVOPS_AGENT_WORKFLOW_GUIDE.md)** - 使用指南
- **VS Code Subagents**: https://code.visualstudio.com/updates/v1_107#_run-agents-as-subagents-experimental
- **Chat Sessions**: https://code.visualstudio.com/docs/copilot/chat/chat-sessions#_contextisolated-subagents

---

**建议**: 对于复杂功能，优先使用 **Subagent 模式**（模板 1），可大幅提升效率！

---

## ⚠️ 重要澄清：Context 隔离机制

根据 [VS Code 官方文档](https://code.visualstudio.com/docs/copilot/chat/chat-sessions#_contextisolated-subagents)：

> "Subagents operate independently from the main chat session and have their own context window. When a subagent completes its task, it returns only the final result to the main chat session."

### 关键理解

#### 1. Context 隔离
- ✅ 每个 subagent 有**独立的 context window**
- ❌ Subagent **不能直接访问**其他 subagent 的 context
- ❌ Subagent **不能直接访问**主 session 的完整对话历史
- ✅ 主 session（orchestrator）充当**协调者**角色

#### 2. 数据传递机制
- Subagent 完成后**只返回最终结果**（如文件路径、Issue ID）
- 主 session 接收结果并**作为输入传递**给下一个 subagent
- 必须**显式传递**所需参数（不能依赖 context 自动共享）

#### 3. 与 Handoffs 的本质区别

| 特性 | Handoffs | Subagents |
|-----|---------|-----------|
| **触发方式** | 用户手动点击按钮 | 自动执行（orchestrator 控制） |
| **Chat Sessions** | 完全独立的多个 sessions | 单一 main session + 隔离的 subagents |
| **结果汇总** | 分散在多个 chat | 集中在 main session |
| **Context** | 每个 session 完全隔离 | 每个 subagent 隔离，但结果返回 main |
| **用户体验** | 需多次交互 | 一次触发完成 |

#### 4. Subagent 的真正优势

**不是**"共享 context"，而是：
- ✅ **自动执行**：无需手动点击按钮
- ✅ **结果汇总**：所有输出集中在主 session
- ✅ **统一历史**：主 session 记录完整流程
- ✅ **Context 优化**：每个 subagent 有干净的 context window

#### 5. 实际影响

在设计 subagent 工作流时，orchestrator（主 session）必须：

```markdown
# 错误理解（假设 context 共享）
runSubagent(DevOps_System_Architect)
# ❌ 期望 Architect 自动知道 PM 创建的文件路径

# 正确理解（显式传递参数）
result_pm = runSubagent(DevOps_Product_Manager, ...)
# result_pm = {req_path: "/docs/requirements/req-xxx.md", issue_id: 101}

runSubagent(DevOps_System_Architect, {
  prompt: f"Based on requirement at {result_pm.req_path}, create design"
  # ✅ 必须显式传递文件路径
})
```

#### 6. 为什么还是比 Handoffs 好？

虽然 context 仍是隔离的，但优势在于：

1. **自动化流程**：Orchestrator 自动管理整个流程
2. **参数传递自动化**：Orchestrator 负责捕获和传递结果
3. **统一追溯**：所有决策和结果在一个 chat 中可见
4. **错误集中处理**：Orchestrator 可立即检测并报告错误

---

## 📊 修正后的对比

| 维度 | Handoffs | Subagents（修正理解） |
|------|---------|---------------------|
| **Context 隔离** | ✅ 完全隔离（独立 sessions） | ✅ 完全隔离（独立 context windows） |
| **触发方式** | ❌ 手动点击 | ✅ 自动执行 |
| **结果位置** | ❌ 分散多个 chat | ✅ 集中主 session |
| **参数传递** | ❌ 用户手动复制 | ✅ Orchestrator 自动 |
| **流程控制** | ❌ 用户控制 | ✅ 程序控制 |
| **错误处理** | ❌ 用户判断 | ✅ Orchestrator 检测 |

---

## 🔄 修正后的工作流理解

```
Main Session (Orchestrator)
│
├─ 1. 接收用户请求: "Execute full workflow for: [Feature]"
│
├─ 2. 调用 runSubagent(DevOps_Product_Manager)
│   ├─ Subagent PM 在独立 context 中工作
│   ├─ 创建 req.md, Issue #101
│   └─ 返回: {req_path, issue_id} → Main Session
│
├─ 3. Main Session 接收 PM 结果
│   ├─ 验证结果是否成功
│   └─ 准备传递给下一个 subagent
│
├─ 4. 调用 runSubagent(DevOps_System_Architect)
│   ├─ Orchestrator 传递: req_path=/docs/requirements/req-xxx.md
│   ├─ Subagent Architect 在独立 context 中工作
│   ├─ 读取文件、创建 design.md
│   └─ 返回: {design_path} → Main Session
│
├─ 5. Main Session 接收 Architect 结果
│   └─ 准备传递给 Planner
│
├─ 6. 调用 runSubagent(DevOps_Tech_Lead_Planner)
│   ├─ Orchestrator 传递: req_path + design_path
│   ├─ Subagent Planner 在独立 context 中工作
│   ├─ 创建 plan.md, Sub-issues
│   └─ 返回: {plan_path, sub_issues[]} → Main Session
│
└─ 7. Main Session 生成最终报告
    ├─ 所有文档路径
    ├─ 所有 Issue URLs
    └─ 下一步建议
```

**关键点**：
- ⚠️ 每个 subagent 的 context 是**隔离的**
- ✅ 但 orchestrator 负责**自动传递**参数
- ✅ 所有**结果集中**在 main session
- ✅ 用户只看到**一个连贯的对话**

---

## ⚠️ 重要澄清：Context 隔离机制

根据 [VS Code 官方文档](https://code.visualstudio.com/docs/copilot/chat/chat-sessions#_contextisolated-subagents)：

> "Subagents operate independently from the main chat session and have their own context window. When a subagent completes its task, it returns only the final result to the main chat session."

**关键理解**：

1. **Context 隔离**：
   - 每个 subagent 有**独立的 context window**
   - Subagent **不能直接访问**其他 subagent 的 context
   - Subagent **不能直接访问**主 session 的完整对话历史

2. **数据传递机制**：
   - 主 session（orchestrator）负责协调
   - Subagent 完成后**只返回最终结果**（如文件路径、Issue ID）
   - 主 session 将这些结果**作为输入传递**给下一个 subagent

3. **优势所在**：
   - ✅ **自动执行**：无需手动点击按钮
   - ✅ **结果汇总**：所有结果集中在主 session
   - ✅ **统一历史**：主 session 记录完整流程
   - ⚠️ **但非共享 context**：需显式传递文件路径等参数

4. **与 Handoffs 的本质区别**：
   - **Handoffs**：完全独立的 chat sessions（用户手动触发）
   - **Subagents**：在主 session 内的隔离 agents（自动触发 + 结果汇总）

**实际影响**：
在设计 subagent prompts 时，必须明确传递所需参数：
```markdown
runSubagent(DevOps_System_Architect, {
  prompt: "Based on requirement at /docs/requirements/req-xxx.md, create design"
  # ☝️ 必须明确传递文件路径，subagent 无法从 PM 的 context 直接获取
})
```
