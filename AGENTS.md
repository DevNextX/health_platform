# Repository Guidelines

## Project Structure & Module Organization
- Backend source under `src/`; Flask entrypoint `src/app.py`, configuration helpers in `src/config.py`, route blueprints in `src/service/`, and data models in `src/models.py`.
- Frontend React app lives in `frontend/`; CRA tooling is in place and the dev proxy targets `http://localhost:5000`.
- Tests reside in `tests/`, with pytest suites at the root and Playwright E2E specs in `tests/e2e/`. Utility scripts live in `tools/` and `scripts/`, and deployment assets in `deploy/`.

## Build, Test, and Development Commands
- `make run` starts the backend via `python -m src.app` with default settings.
- `FLASK_APP=src.app python -m flask run --host=0.0.0.0 --port=5000` launches the hot-reload dev server.
- `python -m pytest tests/ -v` runs all backend tests; focus on individual cases with `python -m pytest path::TestClass::test_case -q`.
- From `frontend/`, run `npm install` once, then `npm start` for local development, `npm test` for unit tests, and `npm run build` for production bundles.
- Execute `make smoke` to perform a quick API health probe before merging.

## Coding Style & Naming Conventions
- Python code follows PEP 8 with 4-space indents; modules use `snake_case.py`, classes `PascalCase`, and functions/variables `snake_case`.
- Flask routes should stay thin; move business logic into services or managers under `src/service/`.
- React components are functional; name files `PascalCase.jsx/tsx`, hooks `useName.js`, and other utilities `camelCase.js`. CRA's ESLint/Prettier defaults apply.

## Testing Guidelines
- Pytest discovers files named `test_*.py`. Reuse fixtures from `tests/conftest.py` to share setup.
- E2E tests require both backend and frontend running; use `cd tests/e2e && npm install && npx playwright install --with-deps && npm run test`.
- Target high-risk areas with focused tests and update or add cases whenever behavior changes.

## Commit & Pull Request Guidelines
- Follow Conventional Commits (e.g., `feat: add appointment scheduler`, `fix: handle empty JWT payload`).
- PRs should summarize changes, reference related issues, and attach test evidence (logs or screenshots). Include reproduction steps or manual checklists when relevant.

## Security & Configuration Tips
- Never commit secrets; load env vars from `.env` (see `.env.example`). Key variables include `SQLALCHEMY_DATABASE_URI`, `JWT_SECRET_KEY`, and `CORS_ORIGINS`.
- SQLite is provisioned automatically in development. For production, configure MySQL credentials and optional TLS via environment variables.
