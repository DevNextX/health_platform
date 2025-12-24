# Architecture

## Executive Summary

The health_platform architecture extends the existing modular monolith built on Flask 3 + React 18 to deliver configurable health threshold governance without disrupting current record capture flows. Threshold profiles are managed by a super administrator, persisted with historical versions, refreshed through deterministic version checks, and enforced consistently across API responses, dashboards, exports, and audits. The design keeps implementation boring and predictable so human teams and AI agents can evolve features safely.

## Project Initialization

First implementation story: **"Bootstrap threshold governance foundation"**. Validate the repo, install dependencies, and seed dev data before wiring new modules.

```cmd
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
npm install --prefix frontend
set PYTHONPATH=.
```

Minimum runtime services: SQLite (dev) or PostgreSQL 15.5 (prod). No additional cache tier is required for the baseline rollout.

## Decision Summary

| Category | Decision | Version | Affects Epics | Rationale |
| --- | --- | --- | --- | --- |
| Architecture Style | Modular monolith (Flask API + React SPA + shared DB) | N/A | Epic 1 · 2 · 3 | Keeps deployment simple while isolating concerns with service/manager layering. |
| Backend Framework | Flask + Flask-SQLAlchemy | Flask 3.0.3 / Flask-SQLAlchemy 3.1.1 | Epic 1 · 2 · 3 | Aligns with existing stack; supports blueprints and layered services. |
| ORM Layer | SQLAlchemy Core/ORM | 2.0.x (bundled with Flask-SQLAlchemy 3.1.1) | Epic 1 · 2 | Enables migrations, JSON columns, and soft validations. |
| Database | PostgreSQL 15.5 (prod) / SQLite 3.41 (dev) | 15.5 / 3.41 | Epic 1 · 2 · 3 | PostgreSQL gives JSONB + row level locks for audit history; SQLite remains for local dev. |
| Cache Strategy | Database-backed version checks with lightweight in-process cache | N/A | Epic 2 | Leverages existing SQL storage; agents read latest version metadata without external services. |
| Frontend Framework | React SPA with React Router | React 18.2.0 / react-scripts 5.0.1 | Epic 1 · 3 | Matches existing create-react-app tooling; simple to extend. |
| UI Toolkit | Ant Design | Ant Design 5.8.6 | Epic 1 · 3 | Provides consistent form validation, data tables, and a11y-ready components. |
| API Contract | REST `/api/v1` JSON payloads | API v1.0 | Epic 2 · 3 | Maintains existing REST semantics with deterministic shapes for agents. |
| Authentication | JWT with role guard (USER/ADMIN/SUPER_ADMIN) | PyJWT 2.9.0 | Epic 1 · 2 · 3 | Reuses infrastructure and enforces super admin-only writes. |
| Observability | Structured logging + audit trail | logging schema 2025.12 | Epic 1 · 2 | JSON logs + persistent audit tables enable compliance checks. |

## Project Structure

```
health_platform/
├── docs/
│   ├── prd.md
│   ├── epics.md
│   └── architecture.md  # this document
├── src/
│   ├── app.py
│   ├── config.py
│   ├── extensions.py
│   ├── models.py
│   ├── service/
│   │   ├── auth_service.py
│   │   ├── admin_service.py
│   │   ├── health_service.py
│   │   └── threshold_service.py  # new blueprint: CRUD + publish endpoints
│   ├── manager/
│   │   ├── health_manager.py
│   │   ├── threshold_manager.py  # new: persistence + validation logic
│   │   └── audit_manager.py      # new helper for audit export pipeline
│   ├── resilience/
│   │   └── __init__.py           # reserved for future circuit breakers / caching helpers
│   ├── utils.py
│   └── security.py
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── SuperAdminSetting.jsx  # extends with ThresholdConfigView
│   │   │   └── HealthRecords.js
│   │   ├── components/
│   │   │   ├── ThresholdForm.jsx
│   │   │   └── ThresholdAuditTable.jsx
│   │   └── services/api.js
│   └── package.json
├── tests/
│   ├── test_admin.py
│   ├── test_health.py
│   ├── test_members.py
│   └── threshold/
│       ├── test_threshold_service.py  # new API tests
│       └── test_threshold_manager.py  # business logic tests
└── deploy/
    ├── k8s-template.yaml
    └── docker-compose.yml
```

## Epic to Architecture Mapping

| Epic | Architecture Scope | Primary Modules | Notes |
| --- | --- | --- | --- |
| Epic 1 · Super Admin Threshold Governance | Threshold UI + persistence + versioning | `threshold_service.py`, `threshold_manager.py`, `frontend/src/pages/SuperAdminSetting.jsx` | Handles draft/save/publish flows, version diffing, and audit exports. |
| Epic 2 · Threshold Publish & Sync | Cache invalidation, API exposure, Self/自己 guard | `resilience/cache.py`, `health_service.py`, `manager/member_manager.py` | Ensures publish invalidates caches, API exposes status/version, Self/自己 guard enforced. |
| Epic 3 · Member Experience & Visualization | UI consumption, status filtering, exports | `frontend/src/pages/HealthRecords.js`, `frontend/src/components/charts/*`, `service/health_service.py` | Applies latest thresholds to forms, charts, exports with consistent status labels. |

## Technology Stack Details

### Core Technologies

- **Backend:** Python 3.11, Flask 3.0.3, Flask-SQLAlchemy 3.1.1, Flask-JWT-Extended 4.6.0, Flask-Limiter 3.7.0.
- **Database:** PostgreSQL 15.5 in production (JSONB for threshold profiles), SQLite 3.41 in development, Alembic migrations for schema evolution.
- **Cache Strategy:** In-process cache with TTL keyed by `threshold_version`; SQL remains the source of truth.
- **Frontend:** React 18.2.0, React Router 6.15, Ant Design 5.8.6, Axios 1.5.0, ECharts 5.4.3.
- **Testing:** Pytest 8.2.2 for backend, React Testing Library for frontend, Playwright for E2E.

### Integration Points

- **Threshold Publish → Readers:** Publishing increments the `threshold_version` column. Clients fetch the active profile and compare versions to detect updates; optional in-process caches invalidate when version changes.
- **Backend → Frontend:** `/api/v1/thresholds/active` returns `{profile, version, updated_at}` consumed by React hooks; responses adhere to ISO 8601 with timezone info.
- **Audit Export:** `/api/v1/admin/thresholds/audit/export` streams UTF-8 BOM CSV using RFC5987 filename headers.
- **Self/自己 Guard:** Manager layer intercepts destructive operations for protected member IDs and returns `SELF_PROTECTED` error codes.

## Novel Pattern Designs

### Threshold Governance Pipeline

- **Purpose:** Provide consistent draft → preview → publish workflow without downtime.
- **Components:**
  - Draft store in `threshold_profiles` table with `status` column (`draft`, `active`).
  - Publish service updates profile, bumps `threshold_version`, writes audit trail.
  - Frontend preview drawer fetches sample records via `/api/v1/thresholds/preview` to simulate statuses.
- **Data Flow:** Super admin saves draft → manager validates ranges and ensures systolic > diastolic, heart rate optional → preview uses current draft values to label sample records → publish sets `effective_at`, increments `threshold_version`, enqueues invalidation.
- **Implementation Guide:**
  1. Add `threshold_profiles` and `threshold_versions` tables with JSON payload column for future schema evolution.
  2. Implement `ThresholdManager.publish(profile_id, actor)` with transaction that writes version, audit, and invalidation message.
  3. Expose `/thresholds/active` endpoint that returns the current `threshold_version`; clients invalidate local cache when the version changes.
  4. Frontend state hook polls `/thresholds/active` (ETag or version header) and invalidates on publish toast.

## Implementation Patterns

- **Naming:**
  - REST paths are plural nouns with hyphenated segments (`/api/v1/threshold-profiles`).
  - Database tables snake_case; foreign keys `<resource>_id`.
  - React components PascalCase; hooks `useThresholdXYZ`.
- **Structure:**
  - Service layer only handles HTTP + validation; threshold business logic resides in managers.
  - Tests colocated under `tests/threshold/` mirroring service/manager modules.
  - Frontend threshold components live under `frontend/src/components/threshold/`.
- **Formats:**
  - API responses wrap data as `{ "data": <payload>, "meta": {"version": <int>} }` and errors as `{ "error": { "code": "...", "message": "..." } }`.
  - Dates serialized using `datetime.now(UTC).isoformat()` including timezone offset.
  - CSV exports include BOM and `filename*="UTF-8''threshold_audit_<date>.csv"` header.
- **Communication:**
  - Version-based invalidation: clients compare `threshold_version` to detect changes.
  - React query invalidation triggered via manual `queryClient.invalidateQueries(['threshold-active'])` call after publish.
- **Lifecycle:**
  - Loading states show AntD `Spin` with `'aria-busy=true'` attribute.
  - Errors escalate through centralized notification service.
  - Retries for publish limited to 3 attempts with exponential backoff using `tenacity`.
- **Location:**
  - Config constants in `src/config.py` under `THRESHOLD_SETTINGS` block.
  - Shared validation helpers in `src/utils.py` for boundary checks.
  - Frontend translation keys under `i18n/locales/*/superAdmin.threshold.*`.
- **Consistency:**
  - All threshold comparisons use integers; convert UI decimals using rounding rules.
  - Status enums: `healthy`, `borderline`, `out_of_range`.
  - Self/自己 guard enforced before any write operations in manager layer.

## Consistency Rules

### Naming Conventions

- API endpoints pluralized (`/thresholds/versions`).
- Database columns snake_case with `_at` suffix for datetimes.
- React files follow `FeatureName.Section.jsx` pattern.

### Code Organization

- Keep managers free of Flask request context to simplify testing.
- Each feature folder exports index barrel for readability.
- Leave room for optional cache clients by injecting a simple cache interface (defaults to in-memory no-op) into managers for testability.

### Error Handling

- All validation errors raise `AppValidationError` mapped to HTTP 400 with localized message keys.
- Publish conflicts raise HTTP 409 with `THRESHOLD_CONFLICT` code.
- If cached data is stale or unavailable, responses include `stale=true` in meta to signal fallback to the last known version.

### Logging Strategy

- Structured JSON logs emitted with fields: `event`, `actor`, `version`, `threshold_status`.
- Audit trail uses database table plus append-only log file rotated daily.
- Frontend logs to browser console only in development; production uses Azure Application Insights integration hook.

## Data Architecture

| Table | Purpose | Key Fields | Relationships |
| --- | --- | --- | --- |
| `threshold_profiles` | Stores current and draft threshold ranges | `id`, `systolic_lower`, `systolic_upper`, `diastolic_lower`, `diastolic_upper`, `heart_rate_lower`, `heart_rate_upper`, `status`, `effective_at`, `version` | `threshold_profiles.id` referenced by `threshold_versions.profile_id` |
| `threshold_versions` | Immutable history of published profiles | `id`, `profile_id`, `version`, `payload_json`, `published_by`, `published_at` | Many-to-one with `threshold_profiles`; join to `users.id` through `published_by` |
| `threshold_audit_log` | Compliance log of every publish/export event | `id`, `action`, `actor_id`, `ip`, `user_agent`, `before_payload`, `after_payload`, `created_at` | Actor references `users.id` |
| `health_records` | Existing patient readings extended with `threshold_status` and `threshold_version` columns | `threshold_status`, `threshold_version` | Many-to-one with `users` and `members` |
| `members` | Member metadata safeguarding Self/自己 | `id`, `full_name`, `status` | `status` + guard logic used during threshold assignment |

Indexes: add `(status, effective_at)` on `threshold_profiles`, `(version DESC)` on `threshold_versions` for fast retrieval, and `(member_id, timestamp)` on `health_records` for trend queries.

## API Contracts

| Method | Path | Auth | Request | Response |
| --- | --- | --- | --- | --- |
| GET | `/api/v1/thresholds/active` | JWT (USER+) | N/A | `{ "data": { "profile": {...}, "version": 7 }, "meta": { "stale": false } }` |
| POST | `/api/v1/admin/thresholds/draft` | JWT (SUPER_ADMIN) | `{ "systolic": {"lower": 90, "upper": 130}, ... }` | 201 with saved draft payload |
| POST | `/api/v1/admin/thresholds/publish` | JWT (SUPER_ADMIN) | `{ "draft_id": 12, "comment": "Align with 2024 ACC/AHA" }` | 200 with new version + publish metadata |
| GET | `/api/v1/admin/thresholds/versions` | JWT (SUPER_ADMIN) | `?page=&size=` | Paginated list of versions with diff metadata |
| GET | `/api/v1/admin/thresholds/audit/export` | JWT (SUPER_ADMIN) | `?format=csv&from=&to=` | Streams CSV/JSON export with `filename*` header |
| GET | `/api/v1/thresholds/preview` | JWT (SUPER_ADMIN) | `?draft_id=&sample=30` | Preview statuses for sample dataset |

Responses include `threshold_version` and `threshold_status` fields to align with exports and dashboards.

## Security Architecture

- JWT tokens signed with `JWT_SECRET_KEY`; refresh rotations bump `token_version`.
- RBAC enforced at service layer: super admins only for draft/publish endpoints; others receive 403.
- Self/自己 guard ensures `member.full_name` equals "Self" or "自己" cannot be removed or altered; operations logged.
- Audit log writes are mandatory and buffered; failure to log triggers transaction rollback.
- Secrets (database credentials, JWT keys) stored in Azure Key Vault via environment variables in production; no dedicated cache credentials required unless a future iteration introduces them.

## Performance Considerations

- Keep published profile cached in-memory with TTL 60 seconds; invalidate when the observed `threshold_version` differs from the cached copy.
- Database indexes ensure threshold version queries remain sub-20ms on 10k records.
- Publish operations wrap in transaction; row-level locking prevents concurrent publishes.
- Frontend caches `/thresholds/active` for 60 seconds using Axios interceptors; invalidated after publish event.
- All threshold computations executed server-side to ensure consistent rounding and to prevent bypasses.

## Deployment Architecture

- Docker compose defines `backend`, `frontend`, and `postgres` services; Azure Container Apps deployment uses separate containers for backend and frontend behind managed ingress.
- Backend container mounts Alembic migrations; entrypoint runs `flask db upgrade` before app start.
- Optional cache tiers (e.g., Redis) can be introduced later if latency requirements tighten.
- GitHub Actions pipeline builds multi-arch images, pushes to Azure Container Registry, and triggers Container Apps revision update.

## Development Environment

### Prerequisites

- Python 3.11+
- Node.js 20 LTS
- Optional local cache tier (e.g., Redis) if benchmarking later proves necessary
- SQLite (auto) or PostgreSQL 15 for integration testing

### Setup Commands

```cmd
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
npm install --prefix frontend
flask db upgrade
```

### Tooling

- VS Code workspace tasks: `Makefile` targets (`make run`, `make smoke`).
- Pre-commit hook recommended for `black` + `eslint` (configure in later sprint).

## Architecture Decision Records (ADRs)

1. **ADR-001:** Retain modular monolith (Flask + React) to minimize operational overhead while introducing clearer internal boundaries for threshold governance.
2. **ADR-002:** Store published threshold payloads in `threshold_versions` (JSONB) to make future schema expansions non-breaking.
3. **ADR-003:** Use database-backed version checks for invalidation to avoid introducing new infrastructure. Evaluate Redis or similar only if throughput and latency metrics warrant it.
4. **ADR-004:** Extend existing REST API (`/api/v1`) instead of introducing GraphQL to keep integration surfaces stable for downstream consumers.
5. **ADR-005:** Enforce Self/自己 guard at manager layer to prevent bypass via alternate service entry points.

---

_Generated by BMAD Decision Architecture Workflow v1.0_
_Date: 2025-12-01_
_For: BMad_
