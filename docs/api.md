# AI Lead Qualification Agent — API Reference

## Overview

The AI Lead Qualification Agent provides a RESTful API built on FastAPI for scoring and triaging inbound B2B sales leads using structured LLM outputs.

- **Base URL:** `http://localhost:8000/api/v1`
- **Format:** All request and response bodies use standard `application/json`.
- **Correlation:** Every API response includes an `X-Request-ID` header. Clients can pass an existing correlation ID in the request header or allow the server to generate one automatically.

---

## Authentication & Security

- LLM credentials (`OPENAI_API_KEY`) are managed entirely server-side via environment configuration.
- Request payloads are validated at the boundary before calling LLM services.
- Sensitive lead attributes (email, phone, text messages) are automatically redacted in server log output to protect PII.

---

## Endpoints

### 1. Health & Readiness

#### `GET /api/v1/health`
Returns basic service health status and environment configuration.

**Response `200 OK`:**
```json
{
  "status": "ok",
  "service": "lead-qualification-agent",
  "environment": "development"
}
```

#### `GET /api/v1/health/live`
Liveness probe for container orchestrators (Kubernetes / Docker Compose).

**Response `200 OK`:**
```json
{
  "status": "ok"
}
```

#### `GET /api/v1/health/ready`
Readiness probe confirming that the service dependency graph is initialized.

**Response `200 OK`:**
```json
{
  "status": "ok"
}
```

---

### 2. Lead Qualification

#### `POST /api/v1/lead/qualify`
Qualifies and scores an inbound sales lead using the configured LLM provider and structured output guardrails.

#### Request Headers

| Header | Type | Required | Description |
| --- | --- | --- | --- |
| `Content-Type` | `application/json` | Yes | Payload format. |
| `X-Request-ID` | `string` | No | Upstream correlation identifier (1–128 chars). |

#### Request Payload (`LeadQualificationRequest`)

At least **one** of `email`, `phone`, `company`, or `message` must be provided.

| Field | Type | Required | Constraints / Description |
| --- | --- | --- | --- |
| `name` | `string` | No | 1–120 characters after trimming. |
| `email` | `string` | No | Valid email syntax; normalized to lowercase. |
| `phone` | `string` | No | 7–30 digits with optional leading `+`. |
| `company` | `string` | No | 1–160 characters after trimming. |
| `designation` | `string` | No | 1–120 characters. |
| `industry` | `string` | No | 1–100 characters. |
| `employees` | `integer` | No | Non-negative integer (0 to 10,000,000). |
| `country` | `string` | No | 2–100 characters. |
| `source` | `string` | No | Lead acquisition channel (1–100 chars). |
| `message` | `string` | No | Free-text message or inquiry (1–4,000 chars). |

#### Success Response (`200 OK` — `LeadQualificationResponse`)

```json
{
  "lead_score": 82,
  "priority": "HOT",
  "buying_intent": "HIGH",
  "intent": "Evaluate AI lead routing tool for CRM integration.",
  "company_size": "MID_MARKET",
  "estimated_deal_size": {
    "currency": "USD",
    "min": 15000.0,
    "max": 40000.0,
    "basis": "Based on 250 employee count and VP-level designation."
  },
  "pain_points": [
    "Manual inbound lead routing delays",
    "Lack of automated qualification"
  ],
  "recommended_next_action": "Schedule a product demo within 24 hours.",
  "sales_summary": "Qualified VP-level decision maker seeking workflow automation.",
  "confidence_score": 0.85,
  "metadata": {
    "request_id": "c7a8e9d0-1234-5678-9abc-def012345678",
    "prompt_version": "lead_qualification_v1",
    "cached": false
  }
}
```

#### Field Definitions

- `lead_score` (0–100): Composite lead score evaluated by LLM rubric.
- `priority` (`HOT` \| `WARM` \| `COLD`): Reconciled sales priority band. `HOT` (75–100), `WARM` (40–74), `COLD` (0–39).
- `buying_intent` (`HIGH` \| `MEDIUM` \| `LOW` \| `UNKNOWN`): Evaluated purchase intention.
- `company_size` (`SOLO` \| `SMB` \| `MID_MARKET` \| `ENTERPRISE` \| `UNKNOWN`): Business size tier.
- `estimated_deal_size`: Object with `currency` (3-letter ISO), `min`, `max`, and evidence `basis`.
- `pain_points`: Array of up to 5 concise pain point strings.
- `recommended_next_action`: Actionable next step for sales representatives.
- `sales_summary`: Executive summary of lead qualification analysis.
- `confidence_score` (0.00–1.00): Measure of evidence sufficiency.
- `metadata`: Contains `request_id`, `prompt_version`, and `cached` indicator.

---

## Error Handling

All errors are returned in a standard envelope format.

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "request_id": "req-12345",
    "details": [
      {
        "location": ["body", "email"],
        "message": "value is not a valid email address",
        "type": "value_error"
      }
    ]
  }
}
```

### Standard Error Codes

| HTTP Status | Error Code | Description |
| --- | --- | --- |
| 422 | `VALIDATION_ERROR` | Request payload failed schema or cross-field validation rules. |
| 415 | `UNSUPPORTED_MEDIA_TYPE` | Content-Type header is not `application/json`. |
| 502 | `INVALID_LLM_RESPONSE` | LLM output failed JSON Schema validation. |
| 502 | `LLM_UNAVAILABLE` | LLM provider service is temporarily unreachable or rate-limited. |
| 503 | `SERVICE_UNAVAILABLE` | LLM API key or required service configuration is missing. |
| 504 | `LLM_TIMEOUT` | Provider request exceeded configured timeout budget. |
| 500 | `INTERNAL_ERROR` | Unexpected internal server error. |
