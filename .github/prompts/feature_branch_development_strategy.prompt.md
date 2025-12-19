```prompt
---
agent: agent
---

# Health Platform Feature Development & Branch Strategy (Prompt Template)

> This file guides GitHub Copilot / Agent to follow standardized branch strategies and development workflows when working on **new features or versions** in this repository. Reference this prompt for any new feature development.

## I. Branch & Environment Strategy

1. **Main Branch (`main`)**:
   - Always kept in a deployable state.
   - Production deployments are made from `main` (typically with tags, e.g., `v1.1.0`).

2. **Feature Branches (`feature/*`)**:
   - Used for new features or significant changes.
   - Naming convention: `feature/<short-kebab-or-snake-name>`, examples:
     - `feature/health-trend-dashboard`
     - `feature/member-tag-filtering`

3. **Fix Branches (`fix/*`)**:
   - Used for bug fixes.
   - Naming convention: `fix/<issue-or-bug-desc>`, examples:
     - `fix/bp-validation-limits`

4. (Optional) Environment Branches:
   - When team/CI requires, you may enable:
     - `develop`: Integration development branch
     - `staging`: Pre-production branch
   - Recommended topology:

     ```text
     main (production-ready)
       ↑
     staging (pre-production)
       ↑
     develop (integration)
       ↑
     feature/* (feature development)
     ```
By default, use lightweight trunk-based mode: `feature/*` → `main`. Unless explicitly requested, assume no environment branches exist.

## II. Unified Feature Development Workflow

> When Agent receives instructions to "develop a new feature", automatically follow these steps and prompt user to confirm current branch and target strategy when needed.

1. **Verify Current Branch & Sync with Main**
   - Command example (executed by user in Terminal 3):

     ```cmd
     git checkout main
     git pull origin main
     ```

2. **Create Feature Branch**
   - Work with user to generate branch name based on brief feature description, e.g., `feature/health-trend-dashboard`.
   - Command example:

     ```cmd
     git checkout -b feature/<short-feature-name>
     git push -u origin feature/<short-feature-name>
     ```

3. **Design Implementation Plan (Minimum Requirements)**
   - Backend:
     - Manager layer changes in `src/manager/`: Data models and business logic.
     - Service/API layer changes in `src/service/`: HTTP routes and parameter validation.
   - Frontend:
     - Add or modify pages/components under `frontend/src/` (React 18 + Ant Design + ECharts + i18next).
   - Testing:
     - Backend unit tests: Add or update Pytest cases in `tests/` directory.
     - If UI behavior involved, update Playwright tests in `tests/e2e/` as necessary.

4. **Implementation & Local Verification**
   - Start the application following `AGENTS.md` / `docs/DEVELOPMENT.md` guidelines:
     - Use the **three separate terminals** model described in `invoke_app_with_different_Terminals.prompt.md`:
       - Terminal 1: Backend only (Flask)
       - Terminal 2: Frontend only (React `npm start`)
       - Terminal 3: For testing and all interactive commands
   - Execute quick test commands in Terminal 3, e.g.:

     ```cmd
     python -m pytest -q
     ```

   - For frontend-backend integration testing, access `http://localhost:3000` via browser and verify expected behavior.

5. **Commit Convention & PR**
   - Git commit messages must follow Conventional Commits:

     ```text
     <type>(<scope>): <description>
     ```

     - `type` examples: `feat` / `fix` / `docs` / `refactor` / `test` / `chore`
     - `scope` recommended to use module or domain name, e.g.: `health` / `admin` / `members` / `frontend`
     - Example:

       ```text
       feat(health): add trend dashboard for blood pressure
       ```

6. **Create Pull Request**
   - Push feature branch to remote: `git push origin feature/<short-feature-name>`
   - Open PR on GitHub targeting `main` (or `develop` if using environment branches)
   - PR title should follow Conventional Commits format
   - Include in PR description:
     - Feature summary
     - Testing performed
     - Screenshots/GIFs if UI changes involved

## III. Testing Requirements

1. **Backend Unit Tests**
   - All new Manager and Service functions must have corresponding pytest cases
   - Maintain test coverage above baseline
   - Run tests in Terminal 3:
     ```cmd
     python -m pytest -v
     ```

2. **Frontend Integration**
   - Test UI components in isolation when possible
   - Verify API integration through browser testing

3. **E2E Tests (When Applicable)**
   - For critical user flows or significant UI changes
   - Update Playwright tests in `tests/e2e/`

## IV. Key Constraints & Conventions

- **Architecture**: Strictly follow Service → Manager → Models layering
- **"Self/自己" Member**: Protected member, cannot be edited/deleted
- **Pagination**: Use `page` + `size` (not `per_page`)
- **Blood Pressure**: 30-250 mmHg, systolic > diastolic
- **Heart Rate**: Optional, 30-150 bpm
- **Tag Filtering**: Exact match + OR semantics, `ensure_ascii=False`
- **Datetime**: Use `datetime.now(UTC)`, not deprecated `utcnow()`
- **CSV Export**: UTF-8 BOM + RFC5987 `filename*`

## V. Documentation Updates

When implementing new features, consider updating:
- `docs/API_Design.md`: If new endpoints added
- `CHANGELOG.md`: Add entry under "Unreleased"
- `README.md`: If user-facing changes
- Relevant requirement/design docs in `docs/`

## VI. Review & Merge Checklist

Before marking PR as ready:
- [ ] All unit tests pass
- [ ] Code follows project conventions
- [ ] No Service layer direct DB access
- [ ] New features have tests
- [ ] Documentation updated if needed
- [ ] Commit messages follow Conventional Commits
- [ ] No secrets or credentials in code

```
