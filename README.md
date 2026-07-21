# AI Lead Qualification Agent

FastAPI foundation for the AI Lead Qualification Agent assignment.

## Current scope

The current implementation includes structured lead qualification through a configurable
OpenAI adapter, with a provider-neutral interface for future providers.

## Run locally

1. Install the project dependencies.
2. Copy `.env.example` to `.env` and adjust values if needed.
3. Run `uvicorn app.main:app --reload`.

## Available endpoints

- `GET /api/v1/health` — basic service status
- `GET /api/v1/health/live` — liveness probe
- `GET /api/v1/health/ready` — readiness probe
- `POST /api/v1/lead/qualify` — structured lead qualification
- `GET /docs` — generated OpenAPI UI

Every response includes `X-Request-ID`. Supply this header on a request to retain an
upstream correlation ID, or omit it to have one generated.

`POST /api/v1/lead/qualify` requires `OPENAI_API_KEY` and accepts the Phase 2 lead
request schema. It returns only the validated `LeadQualificationResponse` schema.
