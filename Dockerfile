# Multi-stage Dockerfile for AI Lead Qualification Agent

# Stage 1: Build virtual environment
FROM python:3.11-slim AS builder

WORKDIR /build

# Install uv for fast, deterministic dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv

# Copy dependency specifications
COPY pyproject.toml uv.lock ./

# Install dependencies into virtualenv
RUN /uv sync --frozen --no-dev

# Stage 2: Runtime image
FROM python:3.11-slim AS runner

WORKDIR /app

# Create non-root user
RUN addgroup --system --gid 1001 appgroup && \
  adduser --system --uid 1001 --gid 1001 appuser

# Copy virtual environment from builder
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application source code and entry points
COPY app /app/app
COPY pyproject.toml /app/pyproject.toml

# Set default environment variables
ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  LEAD_HOST=0.0.0.0 \
  LEAD_PORT=8000

# Change ownership to non-root user
RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

# Healthcheck probe against liveness route
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health/live')" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
