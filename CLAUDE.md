# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Health Platform**: A comprehensive personal health data recording and management platform that provides tracking, analysis, and visualization of health metrics like blood pressure and heart rate.

**Key Features**:
- Multi-user authentication with JWT token management
- Health record CRUD operations with strict validation
- Family member management (simplified household system)
- Data visualization with ECharts integration
- CSV export functionality with proper encoding
- Internationalization support (Chinese/English)
- Responsive design for mobile and desktop
- Real-time data filtering and pagination

**Architecture**: Full-stack application with React frontend and Flask backend, designed for both local development and containerized deployment.

## Essential Development Commands

### Backend Development
```bash
# Setup virtual environment (required)
python -m venv .venv

# Activate virtual environment
# Windows cmd: .\.venv\Scripts\activate.bat
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server (in dedicated terminal)
export PYTHONPATH=.
export FLASK_APP=src.app
python -m flask run --host=0.0.0.0 --port=5000

# Database management
python -m flask db-info    # Show database info and tables
python -m flask db-create  # Create all tables
```

### Frontend Development
```bash
# Setup and start frontend (in separate dedicated terminal)
cd frontend
npm install
npm start  # Development server with hot reload

# Production build
npm run build

# Preview production build
npm install -g serve
serve -s build -l 3000
```

### Testing
```bash
# Backend unit tests (use virtual environment interpreter)
PYTHONPATH=. python3 -m pytest tests/ -v
# Or with virtual environment: .\.venv\Scripts\python.exe -m pytest tests/ -v

# Run specific test class
PYTHONPATH=. python3 -m pytest tests/test_health.py::TestHealthEndpoints -v

# E2E tests (requires backend and frontend running)
cd tests/e2e
npm install
npx playwright install --with-deps
npm run test
```

## Architecture & Key Patterns

### Backend Architecture (Flask)
- **Layered Design**: Service → Manager → Database
  - `src/service/*`: HTTP endpoints, request validation, JWT auth
  - `src/manager/*`: Business logic, database queries
  - `src/models.py`: SQLAlchemy models
- **Authentication**: JWT with refresh token rotation, token versioning for logout-all
- **Database**: SQLAlchemy with automatic table creation, supports SQLite/MySQL/PostgreSQL
- **API Structure**: RESTful endpoints under `/api/v1/`

### Frontend Architecture (React)
- **Component Structure**: Pages → Components → Services
  - `src/pages/*`: Main page components
  - `src/components/*`: Reusable UI components
  - `src/services/api.js`: Axios instance with token refresh interceptors
- **State Management**: React Context for member selection, local state for forms
- **Routing**: React Router with protected routes
- **UI Framework**: Ant Design 5.8.6 with custom styling

### Data Models
- **User**: Authentication, profile data
- **HealthRecord**: Core health metrics (systolic, diastolic, heart_rate, timestamp, tags, note)
- **Household/Member**: Family member management
- **RecordSubject**: Links health records to specific family members

### Authentication Flow
1. Login → JWT access token (30min) + refresh token (7 days)
2. Axios request interceptor adds `Authorization: Bearer <token>`
3. Axios response interceptor handles 401 by refreshing tokens
4. Logout bumps token_version to invalidate all tokens

## Critical Technical Details

### Health Record Validation (Updated)
- **Blood Pressure**: 30-250 mmHg range, systolic must be greater than diastolic
- **Heart Rate**: 30-150 bpm, optional field (can be null/empty)
- **No Auto-Correction**: System preserves user input, only shows validation errors
- **Integer Only**: Decimal values are rejected with specific error messages

### Family Member System
- **Self Member**: Special default member, cannot be deleted, overlays User profile data
- **Member Selection**: Global context for filtering records by family member
- **Data Mapping**: `RecordSubject` table links health records to specific members
- **Lazy Backfill**: Legacy records automatically mapped to Self member

### Internationalization
- **i18next**: Frontend uses react-i18next with language switching
- **Validation Messages**: All error messages support Chinese/English
- **Tag Labels**: Predefined health tags with translations
- **Date/Number Formatting**: Locale-aware formatting with dayjs

### Data Export & Filtering
- **CSV Export**: UTF-8 BOM, RFC5987 filename encoding, member name column
- **Tag Filtering**: OR semantics with exact JSON array matching
- **Date Filtering**: ISO format with timezone handling
- **Pagination**: Backend uses `page` and `size` parameters

### Database Compatibility
- **Development**: SQLite with automatic table creation
- **Production**: MySQL/PostgreSQL with configurable auto-creation
- **Connection Pooling**: Pre-ping enabled, configurable pool recycle
- **Encoding**: UTF-8 with proper collation for Chinese characters

## Development Gotchas

### Python Compatibility
- **Target**: Python 3.8+ compatibility required
- **Type Annotations**: Use `Union[str, int]` instead of `str | int`
- **DateTime**: Use `datetime.timezone.utc` instead of `datetime.UTC`
- **Testing**: Always set `PYTHONPATH=.` for module imports

### Frontend Token Management
- **Infinite Loop Prevention**: Refresh endpoint excluded from response interceptors
- **Token Storage**: localStorage for access_token and refresh_token
- **Logout**: Uses refresh token for secure logout endpoint

### Service Separation
- **Terminal Requirements**: Backend and frontend must run in separate dedicated terminals
- **Port Configuration**: Backend on 5000, frontend on 3000
- **Proxy Setup**: CRA dev server proxies `/api` to `http://localhost:5000`
- **Production**: Use `REACT_APP_API_URL` for custom backend URL

### Member Management
- **Self Protection**: Never allow editing/deleting Self member via API
- **Name Validation**: "Self" and "自己" are reserved names
- **Profile Sync**: User profile changes sync to Self member (height field)

### Form Validation
- **No Auto-Correction**: Use `Input type="number"` instead of `InputNumber` to prevent automatic value correction
- **Real-time Validation**: Custom validators with debounced error state
- **Submit Control**: Disable save button when validation errors exist

### Testing Patterns
- **Backend**: Parametrized tests for validation rules, separate test users
- **E2E**: Playwright with data-testid selectors, headless by default
- **Coverage**: All validation rules must have corresponding test cases

### Database Initialization
- **SQLite**: Always auto-creates tables on startup
- **External DBs**: Creates tables when key tables missing (configurable)
- **Environment Control**: `DB_AUTO_CREATE=1` forces creation, `DB_CREATE_ON_MISSING=0` disables

### CORS & Security
- **Development**: Allows localhost:3000 and 127.0.0.1:3000
- **Headers**: Exposes Content-Disposition for CSV downloads
- **Rate Limiting**: 5/min for auth endpoints, 60/min for others
- **JWT Security**: Token versioning prevents replay attacks

## Quick Reference

### Common File Locations
- Backend services: `src/service/health_service.py`, `src/service/auth_service.py`
- Frontend pages: `frontend/src/pages/HealthRecords.js`, `frontend/src/pages/Dashboard.js`
- API client: `frontend/src/services/api.js`
- Models: `src/models.py`
- Tests: `tests/test_health.py`, `tests/e2e/tests/`
- Translations: `frontend/src/i18n/locales/{en,zh}/translation.json`

### Environment Variables
- `DATABASE_URL`: Database connection string
- `JWT_SECRET`: JWT signing secret
- `CORS_ORIGINS`: Comma-separated allowed origins
- `REACT_APP_API_URL`: Frontend API base URL override

### Validation Error Format
Backend returns structured validation errors:
```json
{
  "error": "Validation failed",
  "details": [
    {"field": "systolic", "message": "Systolic pressure must be between 30-250 mmHg"},
    {"field": "blood_pressure", "message": "Systolic pressure must be greater than diastolic pressure"}
  ]
}
```

### Tag System
- Stored as JSON arrays in database with `ensure_ascii=False`
- Filtering uses OR semantics with exact matching
- Predefined tags with i18n translations
- User can create custom tags via TagSelector component