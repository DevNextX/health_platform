# Repository Guidelines

## Project Structure & Module Organization
- Backend (`src/`): Flask app entry `src/app.py`, configs in `src/config.py`, blueprints under `src/service/`, data models in `src/models.py`.
- Frontend (`frontend/`): React app (CRA). Dev proxy targets `http://localhost:5000`.
- Tests (`tests/`): Pytest suites (unit/integration); E2E under `tests/e2e/` (Playwright).
- Tooling & ops: `tools/`, `scripts/`, `deploy/`, and docs in `docs/`.

## Build, Test, and Development Commands
- Backend run (simple): `make run` (runs `python -m src.app`).
- Backend (Flask dev server): `FLASK_APP=src.app python -m flask run --host=0.0.0.0 --port=5000`.
- Smoke check: `make smoke` (basic API probe).
- Backend tests: `python -m pytest tests/ -v` (use project venv; see `requirements.txt`).
- Frontend dev: `cd frontend && npm install && npm start`.
- Frontend build/test: `npm run build`, `npm test` (from `frontend/`).

## Coding Style & Naming Conventions
- Python: follow PEP 8, 4‑space indents, type hints where practical. Modules `snake_case.py`; classes `PascalCase`; functions/vars `snake_case`.
- Flask: add routes via blueprints in `src/service/`; avoid placing business logic in route handlers—use managers/services.
- JavaScript/React: functional components, components `PascalCase.jsx/tsx`, hooks `useX`, other files `camelCase.js`. ESLint config comes from CRA.

## Testing Guidelines
- Pytest: tests live in `tests/` named `test_*.py`; use fixtures from `tests/conftest.py`.
- Run specific tests: `python -m pytest tests/test_auth.py::TestAuthEndpoints::test_health_check -q`.
- E2E: `cd tests/e2e && npm install && npx playwright install --with-deps && npm run test` (ensure backend and frontend are running).
- CI examples include coverage; local coverage optional.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat: ...`, `fix: ...`, `docs: ...`, etc. (matches current history).
- PRs: include a clear summary, related issue links, test evidence (logs/screenshots), and steps to reproduce/verify.
- Keep changes focused; update docs/tests alongside code.

## Security & Configuration Tips
- Do not commit secrets. Use `.env` locally (see `.env.example`) and GitHub Secrets in CI.
- Key envs: `SQLALCHEMY_DATABASE_URI`, `JWT_SECRET_KEY`, `CORS_ORIGINS`. SQLite is auto‑created in dev; MySQL TLS optional via env.
