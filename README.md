# AI Lead Qualification Agent

An production-grade REST API built with FastAPI and Python for AI-assisted B2B lead qualification, scoring, and triage using LLM structured outputs.

---

## Key Features

- **Structured LLM Qualification:** Uses native OpenAI JSON Schema mode (`gpt-4o-mini`) to extract lead score (0–100), priority (`HOT`/`WARM`/`COLD`), buying intent, company size, deal estimates, pain points, next actions, and confidence scores.
- **Deterministic Priority Reconciliation:** Enforces score-band rules (`HOT` $\ge 75$, `WARM` $40\text{--}74$, `COLD` $< 40$) so score and priority cannot disagree.
- **Prompt Versioning & Anti-Injection:** Delimits lead input within data tags (`<lead_data>`) with system instructions prohibiting prompt injection.
- **Observability & Safe Telemetry:** Structured JSON logging with context-scoped `X-Request-ID` correlation IDs, latency tracking, token usage, estimated USD cost, and automatic PII redaction (email/phone/message).
- **Graceful Error Handling:** Standardized public error envelope (`error.code`, `error.message`, `error.request_id`, `error.details`) for 422 validation, 502 LLM failures, 504 timeouts, and 503 configuration issues.

---

## Architecture Overview

```text
HTTP Client
  │
  ▼
FastAPI Router (POST /api/v1/lead/qualify)
  │
  ├─► Request Context Middleware (X-Request-ID, Latency Logging)
  ├─► Pydantic Request Validation (Boundary Sanitization & Cross-field Rules)
  │
Lead Qualification Service
  │
  ├─► Prompt Registry (lead_qualification_v1)
  ├─► LLM Provider Adapter (OpenAI Structured Output)
  ├─► Result Validation & Priority Reconciliation
  ├─► Usage & Cost Telemetry Recorder (UsageRecord)
  │
  ▼
JSON Response (LeadQualificationResponse + Metadata)
```

---

## Getting Started

### 1. Requirements

- Python 3.11+
- `uv` (Fast Python package installer)

### 2. Environment Setup

Copy `.env.example` to `.env` and set your OpenAI API key:

```bash
cp .env.example .env
```

`.env` configuration example:
```env
LEAD_ENVIRONMENT=development
LEAD_LOG_LEVEL=INFO
LEAD_LOG_FORMAT=json
LEAD_OPENAI_API_KEY=sk-proj-your-api-key
LEAD_OPENAI_MODEL=gpt-4o-mini
LEAD_HOT_LEAD_MIN_SCORE=75
LEAD_WARM_LEAD_MIN_SCORE=40
```

### 3. Run Locally

Start the dev server:
```bash
uv run uvicorn app.main:app --reload --port 8000
```

Access API Documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## API Endpoints

- `GET /api/v1/health` — Basic service health status
- `GET /api/v1/health/live` — Liveness probe
- `GET /api/v1/health/ready` — Readiness probe
- `POST /api/v1/lead/qualify` — Main lead qualification endpoint

### Example Qualification Request

```bash
curl -X POST "http://localhost:8000/api/v1/lead/qualify" \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: req-demo-001" \
  -d '{
    "name": "Aisha Sharma",
    "email": "aisha@example.com",
    "company": "Acme Solutions",
    "designation": "VP of Engineering",
    "industry": "Software",
    "employees": 250,
    "country": "India",
    "message": "Evaluating AI lead qualification tools to integrate with our CRM."
  }'
```

---

## Documentation & Assets

- [API Reference](docs/api.md) — Comprehensive API specifications, request/response models, and error codes.
- [Prompt Engineering Strategy](docs/prompt-design.md) — Prompt structure, scoring rubric, and anti-injection design.
- [Sample Requests & Responses](docs/samples/sample_requests.json) — Executive samples for hot, warm, and cold leads.
- [Postman Collection](postman/lead-qualification.postman_collection.json) — Postman collection for manual API testing.

---

## Running Tests and Linting

Run the test suite:
```bash
uv run pytest -q
```

Run code formatting and lint checks:
```bash
uv run ruff check .
uv run ruff format --check .
```
