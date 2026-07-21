# AI Lead Qualification Agent

A production-grade REST API built with **FastAPI** and **Python** for AI-assisted B2B lead qualification using Large Language Models (LLMs). The service analyzes lead information and returns structured qualification insights, enabling sales teams to prioritize high-value prospects consistently and efficiently.

---

# Features

-AI-Powered Lead Qualification**
  - Uses OpenAI Structured JSON Outputs (`gpt-4o-mini`) for deterministic lead analysis.

- Lead Scoring**
  - Returns a lead score from **0–100**.

- Priority Classification**
  - Automatically classifies leads into:
    - **HOT (≥ 75)**
    - **WARM (40–74)**
    - **COLD (< 40)**

- 🏢 **Business Insights**
  - Buying intent
  - Customer intent
  - Company size
  - Estimated deal size
  - Pain points
  - Recommended next action
  - Sales summary
  - Confidence score

- ✅ **Strict Validation**
  - Pydantic v2 request/response validation.
  - Structured JSON output with deterministic schema.

- ⚡ **Caching**
  - Redis-backed caching
  - In-memory caching
  - Configurable TTL
  - Automatic cache metadata

- 🔐 **Security & Reliability**
  - Prompt injection protection
  - PII redaction
  - Request size limiting (1 MB)
  - Graceful error handling
  - Resource lifecycle management

- 📈 **Observability**
  - Structured JSON logging
  - Request correlation IDs
  - Latency tracking
  - Token usage tracking
  - Cost estimation

- 🐳 **Deployment Ready**
  - Docker
  - Docker Compose
  - Health endpoints
  - Production configuration

---

# Technology Stack

- Python 3.11
- FastAPI
- Pydantic v2
- OpenAI API
- Redis
- Docker
- Pytest
- Ruff
- Uvicorn

---

# Architecture

```text
                 HTTP Client
                      │
                      ▼
      FastAPI Router (/api/v1/lead/qualify)
                      │
                      ▼
      Request Validation (Pydantic)
                      │
                      ▼
        Lead Qualification Service
          │                  │
          │                  ▼
          │           Prompt Registry
          │
          ├────────► Cache
          │      (Redis / Memory)
          │
          ▼
   OpenAI Provider Adapter
          │
          ▼
      OpenAI Structured Output
          │
          ▼
 Response Validation & Reconciliation
          │
          ▼
 Usage Tracking & Telemetry
          │
          ▼
      JSON API Response
```

---

# Project Structure

```text
lead-qualification-agent/
│
├── app/
│   ├── api/
│   ├── core/
│   ├── llm/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   ├── utils/
│   └── main.py
│
├── docs/
│   ├── api.md
│   ├── prompt-design.md
│   └── samples/
│
├── postman/
│
├── tests/
│   ├── integration/
│   ├── unit/
│   └── evaluation/
│
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── .env.example
```

---

# Getting Started

## Requirements

- Python 3.11+
- uv
- Docker (optional)
- Redis (optional)

---

## Environment Setup

Copy the example environment file.

```bash
cp .env.example .env
```

Example:

```env
LEAD_ENVIRONMENT=development
LEAD_LOG_LEVEL=INFO
LEAD_LOG_FORMAT=json

LEAD_OPENAI_API_KEY=sk-proj-xxxxxxxx
LEAD_OPENAI_MODEL=gpt-4o-mini

LEAD_HOT_LEAD_MIN_SCORE=75
LEAD_WARM_LEAD_MIN_SCORE=40

LEAD_CACHE_ENABLED=true
LEAD_CACHE_BACKEND=redis
LEAD_REDIS_URL=redis://localhost:6379/0
LEAD_CACHE_TTL_SECONDS=3600
```

---

# Environment Variables

| Variable | Description |
|------------|----------------------------|
| LEAD_OPENAI_API_KEY | OpenAI API Key |
| LEAD_OPENAI_MODEL | OpenAI model |
| LEAD_CACHE_ENABLED | Enable caching |
| LEAD_CACHE_BACKEND | redis or memory |
| LEAD_REDIS_URL | Redis connection URL |
| LEAD_CACHE_TTL_SECONDS | Cache TTL |
| LEAD_LOG_LEVEL | Logging level |
| LEAD_ENVIRONMENT | Runtime environment |

---

# Running the Application

## Local Development

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Swagger UI

```
http://localhost:8000/docs
```

ReDoc

```
http://localhost:8000/redoc
```

---

## Docker

```bash
docker-compose up --build
```

---

# API Endpoints

| Method | Endpoint | Description |
|----------|------------------------------|----------------------|
| GET | `/api/v1/health` | Health Check |
| GET | `/api/v1/health/live` | Liveness Probe |
| GET | `/api/v1/health/ready` | Readiness Probe |
| POST | `/api/v1/lead/qualify` | Qualify Lead |

---

# Example Request

```bash
curl -X POST http://localhost:8000/api/v1/lead/qualify \
-H "Content-Type: application/json" \
-H "X-Request-ID: req-demo-001" \
-d '{
"name":"Aisha Sharma",
"email":"aisha@example.com",
"company":"Acme Solutions",
"designation":"VP of Engineering",
"industry":"Software",
"employees":250,
"country":"India",
"message":"Evaluating AI lead qualification tools to integrate with our CRM."
}'
```

---

# Example Response

```json
{
  "lead_score": 88,
  "priority": "HOT",
  "buying_intent": "HIGH",
  "intent": "Purchase Evaluation",
  "company_size": "MID_MARKET",
  "estimated_deal_size": "HIGH",
  "pain_points": [
    "Manual lead qualification",
    "CRM integration"
  ],
  "recommended_next_action": "Schedule a product demonstration",
  "sales_summary": "Technical decision maker evaluating AI solutions with clear purchasing intent.",
  "confidence_score": 0.94,
  "metadata": {
    "cached": false,
    "prompt_version": "lead_qualification_v1",
    "request_id": "req-demo-001"
  }
}
```

---

# Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request.",
    "request_id": "req-demo-001",
    "details": {}
  }
}
```

---

# Documentation

| Resource | Description |
|-----------|-------------|
| docs/api.md | API documentation |
| docs/prompt-design.md | Prompt engineering strategy |
| docs/samples/sample_requests.json | Sample requests/responses |
| postman/lead-qualification.postman_collection.json | Postman collection |

---

# Running Tests

Run all tests

```bash
uv run pytest -q
```

Run evaluation harness

```bash
uv run python tests/evaluation/evaluate.py
```

Run lint

```bash
uv run ruff check .
```

Check formatting

```bash
uv run ruff format --check .
```

---

# Evaluation Results

```
48 Tests Passed

Schema Validity Rate : 100%
Priority Consistency : 100%
Score Range Agreement: 100%
Average Latency      : 1.6 ms
```

---

# Production Hardening

The service includes several production-ready optimizations:

- Shared AsyncOpenAI client lifecycle
- Singleton Redis connection pool
- Singleton in-memory cache
- Request body size protection (1 MB)
- Graceful shutdown of shared resources
- Structured logging with correlation IDs
- Prompt versioning
- Automatic PII redaction
- Redis fail-open strategy
- Configurable caching with TTL

---

# Future Improvements

Possible future enhancements include:

- Multi-provider LLM support (Claude, Gemini)
- Streaming responses
- Authentication & authorization
- Rate limiting
- Kubernetes deployment
- Prometheus & Grafana monitoring
- CI/CD with GitHub Actions

---

# Author

**Kuladeep Gompa**

B.Tech – Data Science & Artificial Intelligence  
IIIT Dharwad

GitHub: https://github.com/kuladeepgompa

---

# License

This project was developed as part of an AI Backend Engineering assignment and is intended for educational and portfolio purposes.
