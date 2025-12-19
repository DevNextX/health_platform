# Agent Execution Models: Handoffs vs Subagents

**Document**: Comparison and usage guide for two agent orchestration patterns  
**Date**: 2025-12-19  
**Status**: ✅ Reference Guide

---

## 🎯 Overview

This project supports **two execution models** for DevOps agents:

| Model | Description | Use Case |
|-------|-------------|----------|
| **Handoffs** | Sequential chat sessions (context-isolated) | Interactive refinement, manual control |
| **Subagents** | Single chat session (context-shared) | Automated workflows, batch processing |

---

## 📊 Detailed Comparison

### 1. Context & Memory

| Aspect | Handoffs | Subagents |
|--------|----------|-----------|
| **Chat Session** | New session per agent | Single main session |
| **Context Sharing** | ❌ No (file paths only) | ⚠️ **No** (isolated context windows) |
| **Agent Memory** | Reset for each agent | Each subagent has isolated context |
| **User History** | Separate chat histories | One unified history (in main session) |
| **Result Aggregation** | Scattered across chats | ✅ Centralized in main session |

**Important Clarification** (per [VS Code docs](https://code.visualstudio.com/docs/copilot/chat/chat-sessions#_contextisolated-subagents)):
> "Subagents operate independently from the main chat session and have their own context window."

**Example**:
```
Handoffs:
  Chat 1: @DevOps_Product_Manager [creates req.md]
    ↓ (User clicks "Proceed to Design")
  Chat 2: @DevOps_System_Architect /docs/requirements/req-xxx.md
    ↓ (User clicks "Proceed to Planning")
  Chat 3: @DevOps_Tech_Lead_Planner /docs/design/design-xxx.md

Subagents:
  Main Chat Session: Execute full workflow for: [Feature]
    ├── runSubagent(DevOps_Product_Manager) → isolated context
    │   └── Returns: {req_path} to main session
    ├── Main session passes req_path to next subagent
    ├── runSubagent(DevOps_System_Architect) → isolated context
    │   └── Returns: {design_path} to main session
    └── Main session passes paths to next subagent
    
  Key: Each subagent has isolated context, but results flow back to main session
```

---

### 2. Trigger Mechanism

| Aspect | Handoffs | Subagents |
|--------|----------|-----------|
| **Invocation** | Manual button click | Automatic via `runSubagent` |
| **User Input** | Required at each step | Single input at start |
| **Progression** | User-controlled | System-controlled |
| **Interruption** | Easy (just don't click) | Requires error handling |

**Handoffs Configuration** (in `.agent.md`):
```yaml
handoffs:
  - label: Proceed to Technical Design
    agent: DevOps_System_Architect
    prompt: "Requirements are ready. Please start design."
```

**Subagents Usage** (in workflow prompt):
```markdown
runSubagent({
  agentName: "DevOps_Product_Manager",
  description: "Requirements Analysis",
  prompt: "Analyze: [Feature]"
})
```

---

### 3. Data Passing

| Aspect | Handoffs | Subagents |
|--------|----------|-----------|
| **Primary Method** | File paths | File paths + Orchestrator coordination |
| **Structured Output** | ❌ Not required | ✅ **Required** (for orchestrator) |
| **Validation** | Manual by user | Automatic by orchestrator |
| **Error Propagation** | Silent (next agent may fail) | Immediate (stop workflow) |
| **Context Access** | File system only | ⚠️ File system + orchestrator params |

**Key Insight**: Subagents still require **explicit parameter passing** through the orchestrator, as they have isolated context windows.

**Handoffs** - Data passed via prompt:
```markdown
@DevOps_System_Architect Based on /docs/requirements/req-xxx.md, design the solution
```

**Subagents** - Data coordinated by orchestrator:
```javascript
// Main session (orchestrator) code
const result_pm = await runSubagent({
  agentName: "DevOps_Product_Manager",
  prompt: "Analyze: [Feature]"
});
// result_pm = {req_path: "/docs/requirements/req-xxx.md", issue_id: 101}

// Orchestrator MUST explicitly pass parameters to next subagent
await runSubagent({
  agentName: "DevOps_System_Architect",
  prompt: `Based on requirement at ${result_pm.req_path} (Issue #${result_pm.issue_id}), create design`
  // ⚠️ Cannot rely on subagent "seeing" PM's context automatically
});
```

---

### 4. Error Handling

| Aspect | Handoffs | Subagents |
|--------|----------|-----------|
| **Failure Detection** | User notices manually | Orchestrator detects |
| **Recovery** | Start new chat | Resume from failure |
| **Rollback** | Manual (user judgment) | Programmatic |
| **Partial Success** | User decides to continue | Workflow stops |

**Handoffs** - Manual recovery:
```
Chat 2 fails → User manually goes back to Chat 1 
            → Reviews requirement
            → Retries Chat 2 with updated context
```

**Subagents** - Automatic detection:
```
Step 2 fails → Orchestrator detects error
            → Shows last success (Step 1)
            → Suggests recovery command
            → User can retry or fix issue
```

---

### 5. Traceability

| Aspect | Handoffs | Subagents |
|--------|----------|-----------|
| **History Location** | Multiple chat threads | Single chat thread |
| **Search** | Need to search across chats | Search one conversation |
| **Export** | Export multiple chats | Export one chat |
| **Audit Trail** | Fragmented | Unified |

---

## 🎯 When to Use Each Model

### Use Handoffs When:

✅ **Refinement Required**
- User wants to review and refine each stage
- Requirements may need multiple iterations
- Design needs stakeholder approval

✅ **Learning & Exploration**
- Team is new to the workflow
- Exploring different design options
- Need time to digest each stage

✅ **Manual Control**
- User wants to pause between stages
- Need to coordinate with external systems
- Asynchronous collaboration

**Example Scenarios**:
```markdown
# Scenario 1: Iterative refinement
@DevOps_Product_Manager "Add export feature"
[Review output, discuss with team]
[Click "Proceed to Design" when ready]

# Scenario 2: External approval
@DevOps_System_Architect /docs/requirements/req-export.md
[Wait for architect approval]
[Click "Proceed to Planning" after approval]
```

---

### Use Subagents When:

✅ **Automated Workflows**
- Feature is well-defined (no iteration needed)
- Standard process (requirements → design → plan)
- Time-sensitive delivery

✅ **Batch Processing**
- Multiple similar features
- Consistent workflow execution
- Minimal user intervention

✅ **Complete Traceability**
- Need unified audit trail
- Compliance requirements
- Post-mortem analysis

**Example Scenarios**:
```markdown
# Scenario 1: Well-defined feature
Execute full workflow for: Add CSV export with UTF-8 BOM for health records

# Scenario 2: Bug fix with full context
Execute full workflow for: Fix pagination issue in health records list (currently shows wrong page count)

# Scenario 3: Standard enhancement
Execute full workflow for: Add filter by date range in health dashboard
```

---

## 📚 Usage Patterns

### Pattern 1: Hybrid Approach (Recommended)

Use **Subagents** for the pipeline, then **Handoffs** for implementation:

```markdown
# Step 1: Automated workflow (Subagents)
Execute full workflow for: [Feature]
# → Generates req, design, plan in one go

# Step 2: Manual implementation (Handoffs)
@Developer /docs/plan/plan-xxx.md
# → User reviews each commit
# → Manual testing between phases
```

**Benefits**:
- Fast documentation generation
- Controlled implementation
- Best of both worlds

---

### Pattern 2: Full Automation (Advanced)

Chain all agents including Developer:

```markdown
Execute full workflow AND implement Phase 1 for: [Feature]

Use subagents:
1. DevOps_Product_Manager → Requirements
2. DevOps_System_Architect → Design
3. DevOps_Tech_Lead_Planner → Plan + Issues
4. Developer → Implement Phase 1 (Database)

Stop after Phase 1 for review.
```

**Use Case**: Urgent fixes, well-understood features

---

### Pattern 3: Manual Control (Conservative)

Use Handoffs for all stages:

```markdown
# Step 1
@DevOps_Product_Manager "Add feature X"
[Review, refine, approve]

# Step 2
[Click "Proceed to Design"]
[Review design, discuss, approve]

# Step 3
[Click "Proceed to Planning"]
[Review plan, assign tasks]

# Step 4
@Developer [Implement one task at a time]
```

**Use Case**: Critical features, learning phase

---

## 🔧 Implementation Guide

### Configuring Handoffs

In `.github/agents/[AgentName].agent.md`:

```yaml
---
name: DevOps_Product_Manager
handoffs:
  - label: Proceed to Technical Design
    agent: DevOps_System_Architect
    prompt: "Requirements ready at /docs/requirements/req-[slug].md"
---
```

### Implementing Subagent Workflow

In `.github/prompts/feature-workflow.prompt.md`:

```markdown
Execute full workflow for: {{USER_REQUEST}}

Steps:
1. runSubagent(DevOps_Product_Manager)
   - Input: {{USER_REQUEST}}
   - Output: {req_path, issue_id}

2. runSubagent(DevOps_System_Architect)
   - Input: From context (req_path, issue_id)
   - Output: {design_path, issue_id}

3. runSubagent(DevOps_Tech_Lead_Planner)
   - Input: From context (req_path, design_path, issue_id)
   - Output: {plan_path, sub_issues[]}
```

---

## ✅ Best Practices

### For Handoffs:
1. ✅ Keep handoff prompts clear and actionable
2. ✅ Include file paths in handoff messages
3. ✅ Provide context in each chat session
4. ❌ Don't rely on previous chat memory

### For Subagents:
1. ✅ Validate each subagent output before proceeding
2. ✅ Use structured data passing (JSON)
3. ✅ **Explicitly pass all required parameters** (subagents have isolated context)
4. ✅ Handle errors gracefully (stop and report)
5. ✅ Generate summary report at the end
6. ❌ Don't assume context sharing between subagents
7. ❌ Don't chain too many agents (max 4-5)

---

## ⚠️ Critical Clarification: Context Isolation

Based on [official VS Code documentation](https://code.visualstudio.com/docs/copilot/chat/chat-sessions#_contextisolated-subagents):

> "Subagents operate independently from the main chat session and have their own context window. When a subagent completes its task, it returns only the final result to the main chat session, keeping the main context window focused on the primary conversation."

### What This Means

#### ❌ Common Misconception
"Subagents share context, so later agents can see earlier agents' work automatically"

#### ✅ Actual Behavior
- Each subagent has an **isolated context window**
- Subagents **cannot directly access** other subagents' context
- The **main session (orchestrator)** must explicitly pass data between subagents

### Why Subagents Are Still Better Than Handoffs

Despite context isolation, subagents provide significant advantages:

| Benefit | Explanation |
|---------|-------------|
| **Automated Execution** | No manual button clicks required |
| **Centralized Results** | All outputs visible in one main session |
| **Unified History** | Complete workflow traced in single conversation |
| **Orchestrated Data Flow** | Main session handles parameter passing automatically |
| **Error Detection** | Orchestrator can immediately detect and report failures |
| **Context Optimization** | Each subagent gets a clean context window for focused work |

### Correct Usage Pattern

```markdown
# Orchestrator (Main Session) responsibilities:

1. Invoke first subagent
   runSubagent(DevOps_Product_Manager)
   
2. Capture returned results
   result = {req_path: "/docs/requirements/req-xxx.md", issue_id: 101}
   
3. Explicitly pass to next subagent
   runSubagent(DevOps_System_Architect, {
     prompt: f"Based on {result.req_path} (Issue #{result.issue_id}), create design"
   })
   
4. Repeat: Capture → Pass → Invoke
```

**Key Insight**: The orchestrator acts as a **coordinator**, not a context-sharing medium.

---

## 📖 References

- **Handoffs Documentation**: GitHub Copilot Agent Handoffs
- **Subagents Documentation** (CRITICAL READING): 
  - https://code.visualstudio.com/updates/v1_107#_run-agents-as-subagents-experimental
  - https://code.visualstudio.com/docs/copilot/chat/chat-sessions#_contextisolated-subagents
- **Workflow Prompt**: `.github/prompts/feature-workflow.prompt.md`
- **Agent Configs**: `.github/agents/DevOps_*.agent.md`

---

## 🎓 Decision Matrix

Use this matrix to choose your execution model:

| Question | Answer | Recommended Model |
|----------|--------|-------------------|
| Is the feature well-defined? | Yes | **Subagents** |
| Need multiple iterations? | Yes | **Handoffs** |
| Time-sensitive delivery? | Yes | **Subagents** |
| Team is learning the workflow? | Yes | **Handoffs** |
| Need unified audit trail? | Yes | **Subagents** |
| Requires external approvals? | Yes | **Handoffs** |
| Batch processing multiple features? | Yes | **Subagents** |
| Complex stakeholder coordination? | Yes | **Handoffs** |

---

**Status**: ✅ Reference Guide (Updated with context isolation clarification)  
**Audience**: Development team, Project managers  
**Maintenance**: Update when agent capabilities change  
**Last Updated**: 2025-12-19 (Context isolation clarification added)
