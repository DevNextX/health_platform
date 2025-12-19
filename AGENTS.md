# AI Agents Configuration Guide

This document provides an overview of the custom AI agents used in this project and their coordination workflow.

## 🎯 Overview

This project leverages **GitHub Copilot Custom Agents** to streamline the software development lifecycle. Four specialized agents handle different stages from requirements to implementation:

```
DevOps_Product_Manager → DevOps_System_Architect → DevOps_Tech_Lead_Planner → Developer
    (Requirements)          (Design)                  (Planning + Issues)        (Implementation)
```

**Key Features**:
- ✅ Automated document generation (requirements, design, plan)
- ✅ Automated GitHub Issue/Sub-task creation
- ✅ Seamless agent-to-agent handoff
- ✅ Full traceability from concept to code

---

## 📁 Agent Files Location

```
.github/
├── agents/
│   ├── DevOps_Product_Manager.agent.md       # Requirements analysis
│   ├── DevOps_System_Architect.agent.md      # Technical design
│   ├── Devops_Tech_Lead_Planner.md           # Task breakdown + GitHub Issues
│   └── role-developer.agent.md               # Code implementation
└── prompts/
    ├── sync-issue.prompt.md                  # GitHub Issue sync template
    ├── feature_branch_development_strategy.prompt.md
    └── invoke_app_with_different_Terminals.prompt.md
```

---

## 🤖 Agent Descriptions

### 1. DevOps_Product_Manager

**Role**: Requirements Analyst  
**Focus**: "What & Why" - Business value and scope definition  
**Tools**: `createFile`, `editFiles`, `readFile`, `search`, `github/*`, `runSubagent`

**Responsibilities**:
- Clarify user needs through dialogue
- Define acceptance criteria (AC)
- Identify boundary scenarios and constraints
- Create requirement documents: `/docs/requirements/req-[slug].md`
- Create GitHub Issue (labels: `feature`, `planning`)

**Handoff**: → `DevOps_System_Architect`

---

### 2. DevOps_System_Architect

**Role**: Technical Designer  
**Focus**: "How" - System architecture and component design  
**Tools**: `createFile`, `editFiles`, `readFile`, `search`, `runInTerminal`, `github/*`, `usages`, `problems`

**Responsibilities**:
- Analyze existing codebase
- Design 4 dimensions:
  - Data models (Schema, fields, constraints)
  - API contracts (endpoints, auth, request/response)
  - Component architecture (React components, state management)
  - Integration flow (sequence diagrams, data transformation)
- Create design documents: `/docs/design/design-[slug].md`
- Update GitHub Issue with design links

**Handoff**: → `DevOps_Tech_Lead_Planner`

---

### 3. DevOps_Tech_Lead_Planner

**Role**: Implementation Planner + Issue Manager  
**Focus**: "Steps" - Layer-by-layer task breakdown + GitHub Issue orchestration  
**Tools**: `createFile`, `editFiles`, `readFile`, `search`, `runInTerminal`, `github/*`, `todos`

**Responsibilities**:
- Break design into 4 phases:
  - **Phase 1**: Database & Models
  - **Phase 2**: Backend Logic & API
  - **Phase 3**: Frontend Components
  - **Phase 4**: Testing & Verification
- Create implementation plan: `/docs/plan/plan-[slug].md`
- **NEW**: Automated GitHub Issue management:
  - Create Sub-task Issues for each phase (e.g., `[Phase 1] Database - Add Model`)
  - Update main Issue with checklist (`- [ ] #102 Phase 1: ...`)
  - Post plan summary as Issue comment
- Output all Issue URLs for verification

**Handoff**: → `Developer` (with Issue IDs)

---

### 4. Developer

**Role**: Code Implementer  
**Focus**: "Code" - Write, test, and verify implementation  
**Tools**: `editFiles`, `readFile`, `runInTerminal`, `runTask`, `runTests`, `problems`, `changes`

**Responsibilities**:
- Implement tasks from the plan sequentially
- Follow layer order: Database → Backend → Frontend → Testing
- Write unit tests alongside features
- Commit with Issue references: `feat(xxx): ... (ref #102)`
- Create PRs linking Sub-issues: `Closes #102`

---

## 🔄 Workflow Example

### Scenario: Add "Health Threshold Configuration" Feature

#### Execution Model A: Handoffs (Context-Isolated)

**User initiates**:
```markdown
@DevOps_Product_Manager User wants super admin to configure health thresholds
```

**Flow**:
1. Product_Manager completes requirements → Creates `/docs/requirements/req-xxx.md` + Issue #101
2. **User clicks "Proceed to Design" button** → Opens new chat session
3. System_Architect creates design → Updates `/docs/design/design-xxx.md` + Issue #101
4. **User clicks "Proceed to Planning" button** → Opens new chat session
5. Tech_Lead_Planner creates plan → Creates `/docs/plan/plan-xxx.md` + Sub-issues #102-#105

**Characteristics**:
- ✅ Manual control at each stage
- ✅ User can review and refine between steps
- ❌ Each agent runs in isolated context (no shared memory)
- ❌ Requires multiple user interactions

---

#### Execution Model B: Subagents (Context-Shared) ⭐ Recommended

**User initiates**:
```markdown
Execute the full feature development workflow for: Super Admin can configure health thresholds for blood pressure and heart rate

Use runSubagent to sequentially invoke:
1. DevOps_Product_Manager - Requirements analysis + GitHub Issue creation
2. DevOps_System_Architect - Technical design + Issue update
3. DevOps_Tech_Lead_Planner - Implementation plan + Sub-issues creation

After each step, capture outputs and pass to next agent.
Generate final summary with all links.
```

**Flow** (Single Main Session):
```
Main Chat Session (Orchestrator)
├── runSubagent(DevOps_Product_Manager) [isolated context]
│   ├── Creates /docs/requirements/req-threshold-config.md
│   ├── Creates GitHub Issue #101
│   └── Returns to main: {req_path, issue_id: 101}
│
├── Main session receives PM results
│   └── Prepares parameters for next subagent
│
├── runSubagent(DevOps_System_Architect) [isolated context]
│   ├── Input: req_path from main session
│   ├── Creates /docs/design/design-threshold-config.md
│   ├── Updates Issue #101
│   └── Returns to main: {design_path, issue_id: 101}
│
├── Main session receives Architect results
│   └── Prepares parameters for next subagent
│
├── runSubagent(DevOps_Tech_Lead_Planner) [isolated context]
│   ├── Input: req_path + design_path from main session
│   ├── Creates /docs/plan/plan-threshold-config.md
│   ├── Creates Sub-issues #102-#105
│   ├── Updates Issue #101 with checklist
│   └── Returns to main: {plan_path, sub_issues: [102,103,104,105]}
│
└── Main session generates Summary Report
    ├── All documents: ✅
    ├── GitHub Issues: ✅
    └── Ready for: @Developer
```

**Characteristics**:
- ✅ **Automated** - No manual clicks needed
- ⚠️ **Context Isolation** - Each subagent has isolated context
- ✅ **Result Aggregation** - All outputs centralized in main session
- ✅ **Orchestrated** - Main session coordinates parameter passing
- ✅ **Unified History** - Complete workflow in one chat
- ✅ **Faster** - Complete workflow in one command

**Important Note** (per [VS Code docs](https://code.visualstudio.com/docs/copilot/chat/chat-sessions#_contextisolated-subagents)):
> Subagents have **isolated context windows**. The main session (orchestrator) must explicitly pass data between subagents.

---

### Detailed Example Output

#### Step 1: Requirements (Product_Manager)
**Input**: User requests "Super Admin can configure health thresholds"  
**Output**: 
- `/docs/requirements/req-threshold-config.md`
- GitHub Issue #101 created

```markdown
## Acceptance Criteria
- [ ] AC1: Super Admin can configure BP/HR thresholds in UI
- [ ] AC2: Configuration takes effect immediately on dashboard
- [ ] AC3: All changes logged in audit trail
```

---

#### Step 2: Design (System_Architect)
**Input**: `req-threshold-config.md` + codebase analysis  
**Output**:
- `/docs/design/design-threshold-config.md`
- Issue #101 updated with design link

```markdown
## Data Model
Entity: ThresholdConfig
- systolic_range: JSON {"min": 90, "max": 120}
- status: enum (draft, active, archived)

## API Design
POST /api/v1/superadmin/thresholds
- Auth: @require_role('SUPER_ADMIN')
- Request: {systolic: {min, max}, ...}
```

---

#### Step 3: Planning + Issue Creation (Tech_Lead_Planner)
**Input**: `design-threshold-config.md`  
**Output**:
- `/docs/plan/plan-threshold-config.md`
- **4 Sub-task Issues created**:
  - Issue #102: `[Phase 1] Database - Add ThresholdConfig Model`
  - Issue #103: `[Phase 2] Backend - Implement Threshold Manager`
  - Issue #104: `[Phase 3] Frontend - Build Config Form`
  - Issue #105: `[Phase 4] Testing - E2E Verification`
- Main Issue #101 updated with checklist
- Plan summary posted as Issue comment

```markdown
## Phase 1: Database & Models
- [ ] Task 1.1: Add ThresholdConfig class in src/models.py
      Fields: systolic_range (JSON), status (Enum)
      Verify: Model imports without errors
      
- [ ] Task 1.2: Generate migration script
      Command: flask db migrate -m "add threshold config"
      Verify: Migration file in migrations/versions/
```

---

#### Step 4: Implementation (Developer)
**Input**: `plan-threshold-config.md` + Issue #102  
**Actions**:
1. Implement Task 1.1, 1.2 from Phase 1
2. Run tests: `pytest -v`
3. Commit: `feat(threshold): add config model (ref #102)`
4. Create PR: `Closes #102`
5. After merge → Issue #102 auto-closes, Issue #101 checklist auto-checks

---

## 🎯 Quick Command Reference

### Execution Model A: Handoffs (Manual Control)

**Step-by-step with user review**:
```markdown
# Step 1: Requirements
@DevOps_Product_Manager User wants super admin to configure health thresholds
# [Review output, then click "Proceed to Design"]

# Step 2: Design (new chat session)
# System automatically invokes @DevOps_System_Architect with req path
# [Review design, then click "Proceed to Planning"]

# Step 3: Planning (new chat session)
# System automatically invokes @DevOps_Tech_Lead_Planner with design path
# [Review plan and Issues]

# Step 4: Implementation
@Developer /docs/plan/plan-[slug].md
```

**Use when**: Need to review/refine each stage, learning workflow, requires approval

---

### Execution Model B: Subagents (Automated) ⭐ Recommended

**One-command full workflow**:
```markdown
Execute the full feature development workflow for: [YOUR_FEATURE_DESCRIPTION]

Use runSubagent to sequentially invoke:
1. DevOps_Product_Manager - Requirements analysis + GitHub Issue creation
2. DevOps_System_Architect - Technical design + Issue update
3. DevOps_Tech_Lead_Planner - Implementation plan + Sub-issues creation

After each step, capture outputs (file paths, Issue IDs) and pass to next agent.
Generate a final summary with all document links and Issue URLs.
```

**Examples**:
```markdown
# Full workflow
Execute the full feature development workflow for: Super Admin can configure health thresholds for blood pressure and heart rate

# Skip requirements (doc exists)
Based on existing /docs/requirements/req-xxx.md, execute design and planning workflow using runSubagent

# Resume from design
Based on /docs/requirements/req-xxx.md and /docs/design/design-xxx.md, execute planning workflow using DevOps_Tech_Lead_Planner subagent
```

**Use when**: Well-defined feature, time-sensitive, need unified traceability

---

### Comparison Table

| Aspect | Handoffs | Subagents |
|--------|----------|-----------|
| **Trigger** | Manual clicks | Single command |
| **Context** | Isolated (new chat) | Isolated (but results aggregated) |
| **Control** | User at each step | Automated (orchestrator) |
| **Speed** | Slower | Faster |
| **Result Location** | Scattered across chats | Centralized in main session |
| **Use Case** | Iterative refinement | Batch automation |

**Detailed comparison**: See [AGENT_EXECUTION_MODELS.md](docs/AGENT_EXECUTION_MODELS.md)

**Critical Note**: Both models have context isolation. Subagents' advantage is **automated orchestration** and **centralized results**, not shared context.

---

### Individual Agent Invocation (Direct)
```markdown
@DevOps_System_Architect Based on /docs/requirements/req-xxx.md, design the technical solution
```

### Skip to Planning (Design Already Done)
```markdown
@DevOps_Tech_Lead_Planner /docs/design/design-xxx.md
```

### Implementation Only (Plan Ready)
```markdown
@Developer /docs/plan/plan-xxx.md
```

---

## 📊 Output Structure

```
docs/
├── requirements/           # Product_Manager output
│   └── req-threshold-config.md
├── design/                 # System_Architect output
│   └── design-threshold-config.md
└── plan/                   # Tech_Lead_Planner output
    └── plan-threshold-config.md

GitHub Issues
├── Issue #101: [Feature] Threshold Configuration (Main)
│   ├── Sub-issue #102: [Phase 1] Database
│   ├── Sub-issue #103: [Phase 2] Backend
│   ├── Sub-issue #104: [Phase 3] Frontend
│   └── Sub-issue #105: [Phase 4] Testing
```

---

## ✅ Best Practices

### 1. Follow Agent Sequence
- ✅ **Recommended**: Product_Manager → Architect → Planner → Developer
- ❌ **Avoid**: Asking Architect to break down tasks (that's Planner's job)

### 2. Leverage Auto-Handoff
- ✅ Let agents trigger next agent automatically
- ❌ Manually copy/paste document paths

### 3. Link GitHub Issues
- ✅ Commit messages: `feat(xxx): ... (ref #102)`
- ✅ PR descriptions: `Closes #102`
- ❌ Forgetting to link, losing traceability

### 4. Keep Documents Synchronized
- ✅ Requirement changes? Re-run Product_Manager
- ❌ Directly edit plan without updating design

---

## 🔧 Troubleshooting

### Q: Handoff didn't trigger automatically?
**A**: Check agent's `handoffs` field in `.agent.md` file for correct target agent name.

### Q: GitHub Issues not created?
**A**: Verify Tech_Lead_Planner has `github/*` tool permission and workspace is connected to GitHub.

### Q: Sub-issues not linked to main Issue?
**A**: Check if Sub-issue body contains `Related to #[MAIN_ID]` and main Issue has checklist.

---

## 📚 Related Documentation

- [DEVOPS_AGENT_WORKFLOW_GUIDE.md](./docs/DEVOPS_AGENT_WORKFLOW_GUIDE.md) - Detailed usage guide
- [AGENT_ROLE_OPTIMIZATION.md](./docs/AGENT_ROLE_OPTIMIZATION.md) - Role optimization details
- [CONTRIBUTING.md](./CONTRIBUTING.md) - Code commit conventions

---

**Status**: ✅ Active  
**Last Updated**: 2025-12-19  
**Version**: Health Platform v1.5+
