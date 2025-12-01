---
agent: agent
---
Please analyze the current uncommitted changes in the workspace and generate Git commits following these strict rules:

1. **Atomic Commits**: 
   - Do NOT merge all changes into a single commit.
   - Separate changes by module, feature, or context (e.g., separate documentation updates from code changes, separate backend fixes from frontend tweaks).
   - Create multiple distinct commits if necessary.

2. **Commit Message Convention**:
   - Follow the Conventional Commits format: `<type>(<scope>): <description>`
   - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.
   - Scope: The module or file affected (e.g., `auth`, `ui`, `config`).
   - Description: Concise, imperative mood, no period at the end.

3. **Process**:
   - Analyze `git status` and `git diff`.
   - Group related files.
   - Execute `git add <files>` and `git commit -m "..."` for each group sequentially.
