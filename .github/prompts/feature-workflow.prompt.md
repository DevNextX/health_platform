# Full Feature Development Workflow (Single Context with Subagents)

**Purpose**: Execute complete feature development from requirements to implementation plan in a **single chat session** using VS Code subagents (context-shared).

---

## 📖 Overview

This workflow orchestrates three specialized DevOps agents sequentially using `runSubagent` tool, ensuring:
- ✅ All agents run in the **same context** (shared memory)
- ✅ Automatic progression without manual handoffs
- ✅ Complete traceability in one chat history
- ✅ GitHub Issue integration throughout

---

## 🎯 Quick Start Command

Copy and paste this into Copilot Chat:

```markdown
Execute the full feature development workflow for: [YOUR_FEATURE_DESCRIPTION]

Use runSubagent to sequentially invoke:
1. DevOps_Product_Manager - Requirements analysis + GitHub Issue creation
2. DevOps_System_Architect - Technical design + Issue update
3. DevOps_Tech_Lead_Planner - Implementation plan + Sub-issues creation

After each step, capture outputs (file paths, Issue IDs) and pass to next agent.
Generate a final summary with all document links and Issue URLs.
```

**Example**:
```markdown
Execute the full feature development workflow for: Super Admin can configure health thresholds for blood pressure and heart rate
```

---

## 🔄 Detailed Workflow Steps

### Step 1: Requirements Analysis (Product Manager)

**Subagent**: `DevOps_Product_Manager`

**Prompt**:
```markdown
Analyze the user's request: "[USER_REQUEST]"

Tasks:
1. Engage in dialogue to clarify requirements
2. Identify acceptance criteria and boundary scenarios
3. Create requirement document: /docs/requirements/req-[slug].md
4. Create GitHub Issue with labels: feature, planning
5. Return structured output:
   - req_file_path: <absolute path>
   - issue_id: <number>
   - issue_url: <GitHub URL>
```

**Expected Output**:
- ✅ Requirement document created
- ✅ GitHub Issue #[ID] created
- ✅ Structured response for next agent

---

### Step 2: Technical Design (System Architect)

**Subagent**: `DevOps_System_Architect`

**Prompt**:
```markdown
Based on requirement document at [REQ_FILE_PATH] and Issue #[ISSUE_ID], design the technical solution.

Tasks:
1. Read and analyze the requirement document
2. Analyze existing codebase (src/, frontend/src/)
3. Design 4 dimensions:
   - Data models (Schema, fields, constraints, migrations)
   - API contracts (endpoints, auth, request/response)
   - Component architecture (React components, state management)
   - Integration flow (sequence diagrams, data transformation)
4. Create design document: /docs/design/design-[slug].md
5. Update GitHub Issue #[ISSUE_ID] with design link
6. Return structured output:
   - design_file_path: <absolute path>
   - issue_id: <number>
```

**Expected Output**:
- ✅ Design document created
- ✅ Issue #[ID] updated with design summary
- ✅ Structured response for next agent

---

### Step 3: Implementation Planning (Tech Lead Planner)

**Subagent**: `DevOps_Tech_Lead_Planner`

**Prompt**:
```markdown
Based on requirement at [REQ_FILE_PATH] and design at [DESIGN_FILE_PATH], create a detailed implementation plan.

Tasks:
1. Read requirement and design documents
2. Break down into 4 phases:
   - Phase 1: Database & Models
   - Phase 2: Backend Logic & API
   - Phase 3: Frontend Components
   - Phase 4: Testing & Verification
3. For each task, specify:
   - File paths to modify/create
   - Specific operations
   - Verification steps
4. Create plan document: /docs/plan/plan-[slug].md
5. Create GitHub Sub-task Issues for each phase
6. Update main Issue #[ISSUE_ID] with checklist
7. Post plan summary as Issue comment
8. Return structured output:
   - plan_file_path: <absolute path>
   - main_issue_id: <number>
   - sub_issue_ids: [102, 103, 104, 105]
   - sub_issue_urls: [<URLs>]
```

**Expected Output**:
- ✅ Implementation plan created
- ✅ Sub-task Issues #102-#105 created
- ✅ Main Issue updated with checklist
- ✅ Plan summary posted as comment
- ✅ Structured response with all Issue URLs

---

### Step 4: Summary Report (Orchestrator)

**Generate final summary**:

```markdown
✅ Feature Development Workflow Complete

## Documents Created
- 📋 Requirement: /docs/requirements/req-[slug].md
- 🏗️ Design: /docs/design/design-[slug].md
- 📝 Plan: /docs/plan/plan-[slug].md

## GitHub Issues
- 🎯 Main Issue: #[ID] - [Feature Name]
  - 📌 Sub-issue #102: [Phase 1] Database - [Description]
  - 📌 Sub-issue #103: [Phase 2] Backend - [Description]
  - 📌 Sub-issue #104: [Phase 3] Frontend - [Description]
  - 📌 Sub-issue #105: [Phase 4] Testing - [Description]

## Next Action
Ready for implementation! Use:
@Developer /docs/plan/plan-[slug].md

Or start with specific phase:
@Developer Please implement Issue #102: Database setup
```

---

## 📊 Context Model Comparison

| Aspect | **Handoffs** (Old) | **Subagents** (New) |
|--------|-------------------|---------------------|
| Context | ❌ Isolated (new chat per agent) | ✅ Shared (single chat) |
| Trigger | ❌ Manual button clicks | ✅ Automatic via `runSubagent` |
| Data Passing | ❌ File paths only | ✅ Full context + structured data |
| User Interaction | ❌ Multiple confirmations | ✅ Single command |
| Traceability | ❌ Separate chat histories | ✅ One unified history |
| Error Recovery | ❌ Restart from beginning | ✅ Resume from failure point |
| Execution Speed | ❌ Slower (manual steps) | ✅ Faster (automated) |

---

## ✅ Advantages of Subagent Workflow

1. **Single Entry Point**: One command triggers entire pipeline
2. **Shared Context**: Later agents see earlier outputs directly
3. **Atomic Workflow**: Complete end-to-end or fail together
4. **Better Traceability**: All decisions in one conversation
5. **Faster Iteration**: No navigation between chat sessions
6. **Error Visibility**: Failures are immediate and clear

---

## 🔧 Error Handling

If a subagent fails, the orchestrator should:

1. ⚠️ **Stop immediately** (do not proceed to next step)
2. 📋 **Report failure** clearly
3. 📍 **Show last success** (e.g., "Requirement created, Design failed")
4. 💡 **Suggest recovery** (manual intervention or retry command)

**Example Error Message**:
```
❌ Subagent DevOps_System_Architect failed

Reason: Unable to analyze existing codebase structure in src/models.py
Last Success: Requirements document created at /docs/requirements/req-xxx.md
              GitHub Issue #101 created

Recovery Options:
1. Manual: Review and fix codebase structure, then run:
   @DevOps_System_Architect /docs/requirements/req-xxx.md
   
2. Retry: Provide more context about the issue:
   @DevOps_System_Architect Based on /docs/requirements/req-xxx.md, design focusing on [specific area]
```

---

## 📚 Alternative Usage Patterns

### Pattern A: Full Workflow (Recommended)
```markdown
Execute full workflow for: Add role-based dashboard customization
```

### Pattern B: Skip Requirements (Existing Doc)
```markdown
Based on existing /docs/requirements/req-dashboard-custom.md, execute design and planning workflow using subagents
```

### Pattern C: Resume from Design
```markdown
Based on /docs/requirements/req-xxx.md and /docs/design/design-xxx.md, execute planning workflow using DevOps_Tech_Lead_Planner subagent
```

---

## 🚨 Prerequisites

- ✅ VS Code 1.107+ (Subagent support)
- ✅ GitHub Copilot with workspace context
- ✅ DevOps agents configured in `.github/agents/`
- ✅ GitHub repository connected (for Issue creation)
- ✅ Workspace folders: `docs/requirements/`, `docs/design/`, `docs/plan/`

---

## 📖 References

- **VS Code Subagents**: https://code.visualstudio.com/updates/v1_107#_run-agents-as-subagents-experimental
- **Chat Sessions**: https://code.visualstudio.com/docs/copilot/chat/chat-sessions#_contextisolated-subagents
- **Agent Configurations**:
  - `.github/agents/DevOps_Product_Manager.agent.md`
  - `.github/agents/DevOps_System_Architect.agent.md`
  - `.github/agents/Devops_Tech_Lead_Planner.md`
- **Workflow Guide**: `docs/DEVOPS_AGENT_WORKFLOW_GUIDE.md`

---

**Status**: ✅ Recommended Workflow (VS Code 1.107+)  
**Compatibility**: Requires workspace with DevOps agents configured  
**Use Case**: Complex features requiring requirements → design → planning stages
> Ensure all agents update the SAME GitHub Issue."
