# Software Development Orchestration Workflow

This prompt template orchestrates the full software development lifecycle using specialized subagents. It ensures that Requirements, Design, and Plan are created sequentially and all linked to a single GitHub Issue.

## Trigger
Use this prompt with the **Default Agent** or a **Master Agent**.

## Workflow Steps

### Step 1: Requirement Analysis (Product Manager)
**Instruction**:
"Activate the `Product_Manager` agent.
Task: Analyze the user's request: '{{USER_REQUEST}}'.
1. Discuss and clarify the requirements.
2. Create a requirement document at `/docs/requirements/req-{{SLUG}}.md`.
3. **CRITICAL**: Create a new GitHub Issue (or find existing) and post the requirement summary there.
4. Return the Issue ID and File Path."

### Step 2: Architecture Design (System Architect)
**Instruction**:
"Activate the `System_Architect` agent.
Task: Design the solution for Issue #{{ISSUE_ID}}.
1. Read the requirement file: {{REQ_FILE_PATH}}.
2. Create a design document at `/docs/design/design-{{SLUG}}.md`.
3. **CRITICAL**: Post the design summary and file link to Issue #{{ISSUE_ID}}.
4. Return the Design File Path."

### Step 3: Implementation Planning (Tech Lead Planner)
**Instruction**:
"Activate the `Tech_Lead_Planner` agent.
Task: Plan the implementation for Issue #{{ISSUE_ID}}.
1. Read Requirement: {{REQ_FILE_PATH}} and Design: {{DESIGN_FILE_PATH}}.
2. Create a plan document at `/docs/plan/plan-{{SLUG}}.md`.
3. **CRITICAL**: Post the plan summary and file link to Issue #{{ISSUE_ID}}.
4. Return the Plan File Path."

### Step 4: Execution (Developer) - *Optional / Loop*
**Instruction**:
"Activate the `Developer` agent.
Task: Implement Phase 1 of the plan for Issue #{{ISSUE_ID}}.
1. Read Plan: {{PLAN_FILE_PATH}}.
2. Implement the code and tests.
3. Verify tests pass."

## Usage Example
Copy the following block into the chat to start the process for a new feature:

> **Orchestrate Feature**: "I want to add a new feature: **[Feature Name]**.
> Please run the `Product_Manager` to define requirements and create a GitHub Issue.
> Then, automatically pass the result to `System_Architect` for design, and then to `Tech_Lead_Planner` for planning.
> Ensure all agents update the SAME GitHub Issue."
