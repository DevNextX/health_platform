# Unified Dockerfile for Health Platform (Frontend + Backend)
# Multi-stage build: Stage 1 builds React frontend, Stage 2 runs Flask backend with static files.
# Generated for Issue #89 Azure deployment

# =============================================================================
# Stage 1: Build React Frontend
# =============================================================================
FROM node:18-alpine AS frontend-builder

WORKDIR /frontend

# Copy package files and install dependencies
COPY frontend/package*.json ./
RUN npm ci --only=production

# Copy frontend source and build
COPY frontend/ ./
RUN npm run build

# =============================================================================
# Stage 2: Python Backend with Frontend Static Files
# =============================================================================
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=src.app \
    PYTHONPATH=.

# Security: create non-root user
RUN adduser --disabled-password --gecos "" appuser \
 && apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY run_migrations_manual.py ./

# Copy frontend build from stage 1
COPY --from=frontend-builder /frontend/build ./frontend/build

# Create instance directory for SQLite with proper permissions
RUN mkdir -p /app/instance && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port (App Service will override with PORT env var)
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,sys,urllib.request; \
url=f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/api/healthz'; \
try: \
  with urllib.request.urlopen(url, timeout=3) as r: \
    sys.exit(0 if r.status==200 else 1); \
except Exception: \
  sys.exit(1)"

# Run migrations and start Gunicorn
# Note: Flask dev server is not production-ready; using gunicorn instead
CMD python run_migrations_manual.py && \
    gunicorn --bind=0.0.0.0:${PORT:-8000} \
             --workers=2 \
             --threads=4 \
             --timeout=60 \
             --access-logfile=- \
             --error-logfile=- \
             --log-level=info \
             "src.app:create_app()"
