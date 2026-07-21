# AI Lead Qualification Agent

A production-ready AI-powered REST API built with **FastAPI** that qualifies B2B sales leads using Large Language Models (LLMs). The service analyzes lead information and returns structured qualification insights to help sales teams prioritize prospects consistently and efficiently.

---

## Features

- AI-powered lead qualification using OpenAI Structured Outputs
- Lead scoring (0–100)
- Priority classification (HOT / WARM / COLD)
- Business insights including:
  - Buying intent
  - Customer intent
  - Company size
  - Estimated deal size
  - Pain points
  - Recommended next action
  - Sales summary
  - Confidence score
- Strict request & response validation using Pydantic v2
- Redis and in-memory caching
- Prompt injection protection
- PII redaction
- Structured logging and telemetry
- LLM token usage & cost tracking
- Retry & timeout handling
- Docker & Docker Compose support
- Unit, integration, and evaluation tests
- Health endpoints for monitoring

---

# Tech Stack

| Category | Technology |
|-----------|------------|
| Language | Python 3.11 |
| Framework | FastAPI |
| Validation | Pydantic v2 |
| LLM | OpenAI GPT-4o Mini |
| Cache | Redis |
| Containerization | Docker |
| Testing | Pytest |
| Linting | Ruff |
| Server | Uvicorn |

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
│   ├── unit/
│   ├── integration/
│   └── evaluation/
│
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── .env.example
```

---

# Architecture

```text
                HTTP Client
                     │
                     ▼
         FastAPI REST API
                     │
                     ▼
        Request Validation
          (Pydantic v2)
                     │
                     ▼
     Lead Qualification Service
          │                │
          │                ▼
          │        Prompt Registry
          │
          ├────────► Cache
          │     (Redis / Memory)
          │
          ▼
     OpenAI Provider
          │
          ▼
 Structured JSON Response
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

# Getting Started

## Prerequisites

- Python 3.11+
- uv
- Docker (optional)
- Redis (optional)
- OpenAI API Key

---

## Installation

Clone the repository

```bash
git clone https://github.com/kuladeepgompa/lead-qualification-agent.git
cd lead-qualification-agent
```

Install dependencies

```bash
uv sync
```

---

# Environment Configuration

Copy the example configuration.

```bash
cp .env.example .env
```

Example:

```env
LEAD_APP_NAME=lead-qualification-agent
LEAD_ENVIRONMENT=development

OPENAI_API_KEY=your-api-key

LEAD_LLM_PROVIDER=openai
LEAD_OPENAI_MODEL=gpt-4o-mini

LEAD_CACHE_ENABLED=false
LEAD_CACHE_BACKEND=redis
LEAD_REDIS_URL=redis://localhost:6379/0
```

---

# Running the Application

## Local Development

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Once the server starts:

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
|----------|-----------------------------|-------------------------|
| GET | `/api/v1/health` | Health Check |
| GET | `/api/v1/health/live` | Liveness Probe |
| GET | `/api/v1/health/ready` | Readiness Probe |
| POST | `/api/v1/lead/qualify` | Qualify a Lead |

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
    "request_id": "req-demo-001"
  }
}
```

---

# Documentation

| Resource | Description |
|-----------|-------------|
| `docs/api.md` | Complete API documentation |
| `docs/prompt-design.md` | Prompt engineering strategy |
| `postman/` | Postman collection |
| `tests/evaluation/` | Evaluation dataset |

---

# Testing

Run all tests

```bash
uv run pytest -q
```

Run evaluation harness

```bash
uv run python tests/evaluation/evaluate.py
```

Run Ruff

```bash
uv run ruff check .
```

Verify formatting

```bash
uv run ruff format --check .
```

---

# Production Features

- Shared AsyncOpenAI client
- Singleton Redis connection pool
- Singleton in-memory cache
- Request body size limiting
- Structured JSON logging
- Prompt versioning
- Automatic PII redaction
- Retry & timeout handling
- Redis fail-open strategy
- Configurable cache TTL
- Health monitoring endpoints

---

# Future Improvements

- Multi-provider support (Claude & Gemini)
- Authentication & Authorization
- Rate limiting
- CI/CD with GitHub Actions
- Kubernetes deployment
- Prometheus & Grafana monitoring

---

# Author

**Kuladeep Gompa**

B.Tech – Data Science & Artificial Intelligence  
Indian Institute of Information Technology Dharwad

GitHub: https://github.com/kuladeepgompa

---

# License

This project was developed as part of an AI Backend Engineering assignment and is intended for educational and portfolio purposes.
