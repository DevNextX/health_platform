# GitHub Copilot Custom Agents & Workflows

This directory contains custom agent definitions and workflow prompts designed to streamline the software development lifecycle (SDLC) within VS Code using GitHub Copilot.

## 🤖 Custom Agents

We have defined specialized agents to handle different stages of development. You can invoke them in Copilot Chat using `@AgentName`.

| Agent Name | Role | Responsibility | Input | Output |
| :--- | :--- | :--- | :--- | :--- |
| **`@Product_Manager`** | Product Manager | Requirements analysis, scope definition, business value clarification. | User Idea | `/docs/requirements/req-*.md` + GitHub Issue |
| **`@System_Architect`** | Architect | Technical design, data modeling, API definition, system boundaries. | Requirement Doc | `/docs/design/design-*.md` + Issue Update |
| **`@Tech_Lead_Planner`** | Tech Lead | Task decomposition, implementation planning, phasing. | Design Doc | `/docs/plan/plan-*.md` + Issue Update |
| **`@Developer`** | Developer | Code implementation, unit testing, verification. | Plan Doc | Code + Tests |

## 📝 Workflow Prompts

Prompts are reusable templates that orchestrate multiple agents or perform specific tasks.

| Prompt File | Purpose | Usage |
| :--- | :--- | :--- |
| **`feature-workflow.prompt.md`** | **End-to-End Feature Dev**: Orchestrates PM -> Architect -> Planner -> Developer. | Load file in chat or copy content to drive a full feature lifecycle. |
| **`sync-issue.prompt.md`** | **GitHub Sync**: Helper prompt to sync any document content to a GitHub Issue. | Used internally by agents or manually to update issues. |

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
