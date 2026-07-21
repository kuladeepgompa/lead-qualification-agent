# AI Lead Qualification Agent

FastAPI foundation for the AI Lead Qualification Agent assignment.

## Current scope

Phase 1 provides application configuration, structured logging, request correlation,
versioned routing, and health endpoints. Lead qualification and LLM integration are
intentionally not implemented yet.

## Run locally

1. Install the project dependencies.
2. Copy `.env.example` to `.env` and adjust values if needed.
3. Run `uvicorn app.main:app --reload`.

## Available endpoints

- `GET /api/v1/health` — basic service status
- `GET /api/v1/health/live` — liveness probe
- `GET /api/v1/health/ready` — readiness probe
- `GET /docs` — generated OpenAPI UI

Every response includes `X-Request-ID`. Supply this header on a request to retain an
upstream correlation ID, or omit it to have one generated.
