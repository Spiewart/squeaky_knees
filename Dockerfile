# Pull base image - Alpine for minimal memory footprint
# Alpine reduces image size by ~60% compared to slim, critical for low-memory environments
FROM python:3.13-alpine

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies - Alpine uses apk instead of apt
# PostgreSQL dev libraries needed for psycopg PostgreSQL adapter
RUN apk add --no-cache \
    build-base \
    postgresql-dev \
    gettext \
    libffi-dev \
    && rm -rf /var/cache/apk/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy project
COPY . .

# Expose port
EXPOSE 8000

# Run gunicorn with single worker for low-memory environments
# Use 1 worker for droplets with <1GB RAM to avoid OOM kills
CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "120", "config.wsgi:application"]
