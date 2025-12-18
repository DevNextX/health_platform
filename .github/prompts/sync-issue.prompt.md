# Sync to GitHub Issue Prompt

This prompt is designed to be used by any agent (PM, Architect, Planner) to synchronize their generated documentation (Requirements, Design, Plan) to a GitHub Issue.

## Usage
Load this prompt and provide:
1. The content or file path of the document.
2. The GitHub Issue ID (or ask to create one).

## Instructions for the Agent

1.  **Identify Context**:
    - Determine if an Issue ID is provided.
    - If NO Issue ID: Use `mcp_github_search_issues` to find a relevant issue based on the document title. If none found, use `mcp_github_create_issue` with the document title and a summary.
    - If Issue ID provided: Use it.

2.  **Format Comment**:
    - Create a markdown comment that summarizes the document.
    - Include a link to the file path (e.g., `[Requirement Doc](docs/requirements/req-xyz.md)`,`[Design Doc](docs/design/design-xyz.md)`,`[Plan Doc](docs/plan/plan-xyz.md)`).
    - **Important**: If the content is short (< 500 words), include the full text in the comment. If long, provide a high-level summary and the file link.

3.  **Execute**:
    - Use `mcp_github_add_issue_comment` to post the comment to the issue.
    - output the issue url to the user.

4.  **Verify**:
    - Confirm to the user that the issue has been updated.
