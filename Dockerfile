# ── Builder stage ─────────────────────────────────────────────────────────────
# Compiles psycopg[c] and installs the venv. Build tools stay out of the
# runtime image, which keeps it small for the low-memory Droplet.
FROM python:3.13-alpine AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Build dependencies (Alpine): compiler + PostgreSQL/ffi headers
RUN apk add --no-cache \
    build-base \
    postgresql-dev \
    libffi-dev

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies into /app/.venv (cached layer: only re-runs when
# pyproject.toml or uv.lock change, not on every code edit)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.13-alpine

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    UV_NO_SYNC=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# Runtime libraries only: libpq for psycopg, gettext for i18n
RUN apk add --no-cache \
    libpq \
    gettext

# uv is needed at runtime because deploy runs "uv run python manage.py
# migrate" inside the container. UV_NO_SYNC makes uv use the prebuilt
# venv as-is instead of re-syncing (which would pull dev deps at startup).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy the prepared virtualenv, then the project
COPY --from=builder /app/.venv /app/.venv
COPY . .

EXPOSE 8000

# Single worker for <1GB RAM droplets, but with threads so one slow
# request (e.g. a Mailgun API call) doesn't block the whole site.
# --max-requests recycles the worker periodically to cap memory growth;
# --worker-tmp-dir /dev/shm avoids disk-backed heartbeat stalls.
CMD ["gunicorn", \
    "--bind", "0.0.0.0:8000", \
    "--workers", "1", \
    "--threads", "4", \
    "--worker-tmp-dir", "/dev/shm", \
    "--max-requests", "1000", \
    "--max-requests-jitter", "100", \
    "--timeout", "120", \
    "config.wsgi:application"]
