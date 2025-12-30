# GitHub Copilot Custom Agents & Workflows

This directory contains custom agent definitions and workflow prompts designed to streamline the software development lifecycle (SDLC) within VS Code using GitHub Copilot.

## 🤖 Active Agents (role-* only)

Use the role-prefixed agents below as the single source of truth. `Deprecated_*` agents are legacy and should not be invoked.

| Agent Name | Role | Responsibility | Input | Output |
| :--- | :--- | :--- | :--- | :--- |
| **`@Product_Manager`** | Product Manager | Requirements analysis, scope definition, business value clarification. | User Idea | `/docs/requirements/req-*.md` + GitHub Issue |
| **`@System_Architect`** | Architect | Technical design, data modeling, API definition, system boundaries. | Requirement Doc | `/docs/design/design-*.md` + Issue Update |
| **`@Tech_Lead_Planner`** | Tech Lead | Task decomposition, implementation planning, phasing. | Design Doc | `/docs/plan/plan-*.md` + Issue Update |
| **`@Developer`** | Developer | Code implementation, unit testing, verification. | Plan Doc | Code + Tests |

### 流程与 Issue 规范
- 主 Issue 在 `@Product_Manager` 阶段创建/确认，贴上 `/docs/requirements/req-*.md` 链接和摘要。
- `@System_Architect`、`@Tech_Lead_Planner`、`@Developer` 依次在同一个主 Issue 更新设计/计划/进度与验证摘要；默认不新开 Issue。
- 若需要拆分大任务，`@Tech_Lead_Planner` 可创建子 Issue，并在计划中标注关联；开发完成后 `@Developer` 需要回写主/子 Issue 状态与测试要点。
- 每个阶段的输入 = 上一阶段文档 + 主 Issue 最新信息；文档与 Issue 需互相引用，保持链路可追踪。

## 📝 Workflow Prompts

Prompts are reusable templates that orchestrate multiple agents or perform specific tasks.

| Prompt File | Purpose | Usage |
| :--- | :--- | :--- |
| **`feature-workflow.prompt.md`** | **End-to-End Feature Dev**: Orchestrates PM -> Architect -> Planner -> Developer. | Load file in chat or copy content to drive a full feature lifecycle. |
| **`sync-issue.prompt.md`** | **GitHub Sync**: Helper prompt to sync any document content to a GitHub Issue. | Used internally by agents or manually to update issues. |

### Subagent handoff (runSubagent)
- Default path: `@Product_Manager` → `@System_Architect` → `@Tech_Lead_Planner` → `@Developer`.
- When chaining automatically, prefer `runSubagent` with the target agent name and the artifact path (req/design/plan) so state is preserved.
- If you need to jump midstream (e.g., already have a design), invoke the next role directly with the relevant doc path.

### Doc output locations
- Requirements: `/docs/requirements/req-<slug>.md`
- Design: `/docs/design/design-<slug>.md`
- Plan: `/docs/plan/plan-<slug>.md`
- Other documents should stay within their dedicated folders (avoid adding new top-level `.md` files under `docs/`).

## 🔧 可选辅助 Agent（待定）
- 如需云上环境准备或 CI/CD 配置，可新增专职 Agent（例如 `Infra_Expert`, `DevOps_Engineer`）。
- 这些 Agent 不参与主开发流程（PM → Architect → Planner → Dev），但可在需要时被调用；若创建，请指定输出目录（如 `/docs/ops/`, `/docs/workflow/`）并在主 Issue 记录结果。

## 🚀 How to Use

### 1. Start a New Feature (The "One-Click" Way)
1. Open Copilot Chat.
2. Type `#file:feature-workflow.prompt.md` to load the workflow context.
3. Enter your request:
   > "I want to add a [Feature Name]. Please execute the workflow."

### 2. Manual Interaction
You can also call agents individually:
- **PM**: `@Product_Manager I have an idea for...`
- **Architect**: `@System_Architect Please design based on req-xyz.md...`
- **Planner**: `@Tech_Lead_Planner Create a plan for design-xyz.md...`
- **Dev**: `@Developer Start coding phase 1 of plan-xyz.md...`

## 📂 Directory Structure
- `.github/agents/`: Agent definition files (`*.agent.md`).
- `.github/prompts/`: Reusable prompt templates.
