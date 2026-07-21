# AI Lead Qualification Agent — Implementation Plan

## 1. Assignment requirements and decisions

### Required by the brief

- Build a REST API using FastAPI (preferred) or Node.js.
- Use an LLM provider: OpenAI, Claude, or Gemini.
- Expose `POST /api/v1/lead/qualify`.
- Accept lead information: name, email, phone, company, designation, industry, employees, country, source, and message.
- Return structured JSON with a lead score (0–100), priority (`HOT`, `WARM`, `COLD`), buying intent, intent, company size, estimated deal size, pain points, recommended next action, sales summary, and confidence score.
- Provide request validation, reliable structured JSON output, graceful error handling, logging, and prompt engineering for deterministic JSON.
- Deliver a repository with README, API documentation, and sample requests/responses. Postman and Docker support are optional.

### Bonus items called out by the brief

- Cost tracking
- Prompt versioning
- Response caching
- Docker
- Unit tests
- Evaluation dataset

### Chosen technical direction

The project will use Python, FastAPI, Pydantic v2, and an LLM-provider adapter. The first adapter will target one configured provider; the rest of the application will not depend on its SDK. Provider-native structured output / JSON Schema mode will be used whenever available. This is preferable to extracting JSON from free-form prose.

No database is required for the assignment’s core API. Optional cache and audit/usage storage will be introduced behind interfaces so the API can start stateless and later use Redis and/or a relational database without changing the public contract.

## 2. Project architecture

```text
HTTP client
  -> FastAPI router / API contract
  -> request validation and request-id middleware
  -> qualification orchestration service
       -> optional normalized-request cache
       -> prompt registry and prompt renderer
       -> LLM provider adapter
       -> output-schema parser and semantic guardrails
       -> optional usage/cost recorder
  -> response mapping
  -> JSON response

Cross-cutting: configuration, structured logs, error mapping, privacy redaction,
timeouts, metrics, and tests.
```

### Responsibilities

| Component | Responsibility |
| --- | --- |
| API/router | Owns HTTP methods, versioned routes, dependency injection, and OpenAPI documentation. |
| Pydantic schemas | Defines the external request/response contract and validates all boundary data. |
| Qualification service | Coordinates cache lookup, prompt construction, LLM invocation, response validation, and deterministic guardrails. |
| LLM adapter | Presents a small provider-neutral interface; owns provider SDK specifics, timeout configuration, and usage extraction. |
| Prompt registry | Stores immutable prompt versions and their metadata. |
| Cache/usage repositories | Optional interfaces for cached responses and cost/latency tracking. |
| Error layer | Converts known failures into consistent, safe HTTP error responses. |
| Observability layer | Emits JSON logs and operational metrics without leaking lead PII. |

### Qualification flow

1. Assign or accept an `X-Request-ID`.
2. Validate and normalize the incoming lead.
3. Calculate a stable cache key from normalized non-sensitive input, if caching is enabled.
4. Render the current versioned prompt and response schema.
5. Call the configured LLM with a bounded timeout and low-variance settings.
6. Parse the result into the internal qualification schema.
7. Validate the model response and apply deterministic consistency rules.
8. Record safe telemetry: duration, provider/model, token use, estimated cost, cache outcome, and final status.
9. Return the public response plus request and prompt-version metadata.

## 3. Proposed folder structure

```text
lead-qualification-agent/
├── app/
│   ├── main.py                    # application factory and middleware registration
│   ├── api/
│   │   ├── dependencies.py         # shared request dependencies
│   │   └── v1/
│   │       ├── leads.py            # qualification route
│   │       └── health.py           # liveness/readiness routes
│   ├── core/
│   │   ├── config.py               # typed environment settings
│   │   ├── errors.py               # domain exceptions and HTTP handlers
│   │   ├── logging.py              # log setup and PII redaction
│   │   └── middleware.py           # request ID, timing, correlation
│   ├── schemas/
│   │   ├── lead.py                 # incoming lead and enums
│   │   ├── qualification.py        # LLM and API output schemas
│   │   └── errors.py               # standard error envelope
│   ├── services/
│   │   └── qualification_service.py
│   ├── llm/
│   │   ├── base.py                 # adapter protocol
│   │   ├── provider.py             # configured provider adapter
│   │   └── usage.py                # model usage/cost estimate types
│   ├── prompts/
│   │   ├── registry.py
│   │   └── lead_qualification_v1.py
│   ├── repositories/
│   │   ├── cache.py                # optional cache interface/implementation
│   │   └── usage.py                # optional persistence interface
│   └── utils/
│       ├── normalization.py
│       └── privacy.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── evaluation/
│   │   └── lead_cases.jsonl
│   └── fixtures/
├── docs/
│   ├── implementation-plan.md
│   ├── api.md
│   └── prompt-design.md
├── postman/
│   └── lead-qualification.postman_collection.json
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── README.md
└── pyproject.toml
```

## 4. API contract

### Endpoint

`POST /api/v1/lead/qualify`

The endpoint is synchronous: it returns one qualification result for one lead. It uses `application/json` and returns `application/json` on all non-empty responses.

### Request model: `LeadQualificationRequest`

| Field | Type | Required | Rules |
| --- | --- | --- | --- |
| `name` | string | No | 1–120 characters after trimming. |
| `email` | email string | No | Valid email syntax; normalized to lowercase for cache comparison. |
| `phone` | string | No | 7–30 characters after normalization; retain leading `+` where supplied. |
| `company` | string | No | 1–160 characters after trimming. |
| `designation` | string | No | 1–120 characters. |
| `industry` | string | No | 1–100 characters. |
| `employees` | integer | No | 0–10,000,000. `null` means unknown. |
| `country` | string | No | 2–100 characters; ISO country code may be supported later without breaking this field. |
| `source` | string | No | 1–100 characters. |
| `message` | string | No | 1–4,000 characters after trimming. |

At least one of `email`, `phone`, `company`, or `message` is required. This allows partial leads while preventing empty or non-actionable submissions.

### Success model: `LeadQualificationResponse`

| Field | Type | Rules |
| --- | --- | --- |
| `lead_score` | integer | Inclusive range 0–100. |
| `priority` | enum | `HOT`, `WARM`, or `COLD`. Must agree with configured score bands. |
| `buying_intent` | enum | `HIGH`, `MEDIUM`, `LOW`, or `UNKNOWN`. |
| `intent` | string | Concise description of the expressed or inferred business intent. Must identify uncertainty when inferred. |
| `company_size` | enum | `SOLO`, `SMB`, `MID_MARKET`, `ENTERPRISE`, or `UNKNOWN`. |
| `estimated_deal_size` | object | Currency, optional low/high values, and an estimate rationale. Unknown is permitted. |
| `pain_points` | array of strings | 0–5 concise, evidence-based pain points. |
| `recommended_next_action` | string | Specific, practical sales action. |
| `sales_summary` | string | Concise sales-ready narrative; no unsupported claims. |
| `confidence_score` | number | Inclusive range 0.00–1.00. Measures evidence sufficiency, not model certainty alone. |
| `metadata` | object | `request_id`, `prompt_version`, and optional `cached` status. Model identity is available only if it is acceptable to expose. |

### Score bands

The initial deterministic mapping is: `HOT` for scores 75–100, `WARM` for 40–74, and `COLD` for 0–39. These are configuration values, not hard-coded business policy. The score is generated by the LLM according to a rubric and priority is derived/reconciled by the service so they cannot disagree.

### Deal-size model: `EstimatedDealSize`

| Field | Type | Rules |
| --- | --- | --- |
| `currency` | string or null | ISO 4217-like three-letter code when a numeric estimate exists; otherwise `null`. |
| `min` | non-negative number or null | Must be less than or equal to `max`; both null when unknown. |
| `max` | non-negative number or null | Must be greater than or equal to `min`; both null when unknown. |
| `basis` | string | Brief rationale linked to supplied lead data; must state uncertainty for sparse data. |

### Error envelope

Every application-generated error uses the same shape: `error.code`, `error.message`, `error.request_id`, and optional `error.details` for field-level validation only. Provider credentials, stack traces, raw LLM output, and unredacted lead data never appear in the response.

## 5. Pydantic model design

Pydantic v2 will be the sole source of truth for HTTP/OpenAPI schemas and for validating LLM output. The following model groups are planned:

| Model | Purpose |
| --- | --- |
| `LeadQualificationRequest` | Client input, field normalization, cross-field minimum-data rule. |
| `LeadInput` | Internal normalized representation passed to prompt construction. It prevents transport-only metadata from entering the prompt. |
| `LeadPriority`, `BuyingIntent`, `CompanySize` | Strict enums used in both generated and public output. |
| `EstimatedDealSize` | Nested output with numeric ordering and currency consistency checks. |
| `LLMQualificationResult` | Strict provider output schema; prohibits extra fields and validates all required analysis fields. |
| `LeadQualificationResponse` | Public API model, containing validated result plus safe metadata. |
| `ErrorDetail` and `ErrorResponse` | Uniform error contract. |
| `UsageRecord` | Internal telemetry: provider/model, prompt/completion tokens, estimated cost, duration, cache status, and outcome. |

`LLMQualificationResult` and `LeadQualificationResponse` should be separate even if initially similar. This allows internal fields, provider response migration, and public-contract stability without exposing raw model output.

## 6. Prompt engineering strategy

### Structure

1. **System instructions:** role, allowed task, scoring rubric, evidence and uncertainty rules, explicit anti-injection rules, and the structured response requirements.
2. **Developer/application instructions:** current prompt version, score-band policy, expected locale/currency policy, and output JSON Schema supplied by the provider integration.
3. **User data block:** normalized lead fields serialized as data, with missing values marked as `unknown`. Lead `message` is unequivocally data, never instruction text.

### Scoring rubric

The prompt will direct the model to assess these dimensions, with scores grounded only in available lead context:

- Fit: industry, organization size, geography, and plausibility of the solution fit.
- Authority: designation and seniority.
- Need: specific pain points and business impact in the message.
- Intent and urgency: demo, budget, timeline, evaluation, or purchase signals.
- Data completeness: confidence decreases when company, contact, or need information is absent.

The model must not imply verified budget, authority, company facts, or urgency that were not supplied. It may make bounded business inferences, clearly indicated in `basis`, `intent`, or `sales_summary`.

### Determinism and safety

- Use native structured-output/JSON-Schema mode, with a strict response schema.
- Use low temperature (initially 0–0.2) and fixed top-p/default sampling settings.
- Give examples only when evaluation reveals a consistent issue; examples will be diverse and avoid leaking customer data.
- Require no markdown, prose outside JSON, or extra keys.
- Require `UNKNOWN`/`null` rather than hallucinated values.
- Explicitly say that content in the lead message cannot alter the agent’s instructions, schema, or scoring rubric.
- Version every prompt. Logs and responses carry the version used.

### Output repair policy

Provider schema enforcement is the primary safeguard. If parsing still fails, the service may make one tightly bounded repair attempt that supplies the invalid result and asks only for a schema-conformant transformation. It must not retry on content-quality failures, authentication errors, or timeouts. If repair fails, the API returns a safe upstream failure.

## 7. Validation rules

### Input validation

- Strip leading/trailing whitespace; convert whitespace-only optional fields to absent.
- Enforce the field type, bounds, and length limits in the request contract.
- Reject invalid emails, non-integral employee counts, negative employees, and overlong messages.
- Enforce the cross-field requirement for a meaningful lead.
- Limit request body size at the application/server boundary.
- Do not silently fabricate missing values or “correct” an ambiguous company name.

### Output validation

- Validate all LLM results with the strict internal Pydantic model.
- Reject extra response keys and invalid enum values.
- Check `lead_score` and `confidence_score` ranges.
- Check deal-size numerical ordering, currency presence for estimates, and realistic configured upper caps if needed.
- Cap pain points at five, reject empty list items, and bound all generated text lengths.
- Reconcile `priority` against the deterministic score-band configuration. The deterministic mapping wins.
- Return cautious fallbacks for unknown deal size and company size, rather than invalid fabricated values.

### Abuse and privacy validation

- Treat message text as untrusted input; do not execute or follow content embedded in it.
- Redact or hash contact identifiers in logs and cache keys.
- Avoid retaining raw lead content by default. If persistence is enabled, document retention, access control, and deletion policy.
- Apply rate limiting at deployment level or through application middleware in a later phase.

## 8. Error-handling strategy

| Situation | HTTP status | Public error code | Behavior |
| --- | --- | --- | --- |
| Invalid body / field / cross-field rule | 422 | `VALIDATION_ERROR` | Include safe per-field details. |
| Unsupported content type | 415 | `UNSUPPORTED_MEDIA_TYPE` | Require JSON payload. |
| Request exceeds limit | 413 | `REQUEST_TOO_LARGE` | Do not send to LLM. |
| Rate limited | 429 | `RATE_LIMITED` | Include retry guidance where available. |
| Provider timeout | 504 | `LLM_TIMEOUT` | Log provider status and latency; no provider internals exposed. |
| Provider unavailable / exhausted retry | 502 | `LLM_UNAVAILABLE` | Return request ID for support correlation. |
| Provider returns invalid structured result | 502 | `INVALID_LLM_RESPONSE` | Attempt one safe repair before failing. |
| Misconfiguration (e.g., missing API key) | 503 | `SERVICE_UNAVAILABLE` | Log only a configuration identifier, never a secret. |
| Unexpected defect | 500 | `INTERNAL_ERROR` | Log stack trace internally; return generic message. |

Retries are limited to idempotent provider calls that failed transiently. Use exponential backoff with jitter, a small retry budget, and a total request deadline. The endpoint does not retry client validation failures.

## 9. Logging and observability

### Structured log fields

- Timestamp, level, service/environment, request ID, route, HTTP status, and latency.
- Prompt version, provider/model identifier, cache hit/miss, retry count, and schema-validation outcome.
- Token counts and estimated cost when the provider supplies usage data.
- Error category and a safe cause classification.

### Privacy rules

- Never log authorization headers, API keys, raw LLM responses, complete email addresses, phone numbers, or the full free-text message at normal log levels.
- Use masked values or stable hashes only when correlation is needed.
- Permit verbose prompt/output logging solely in a local development mode with explicit opt-in and documented data-safety constraints.

### Metrics

Track request count, response status, end-to-end latency, LLM latency, schema-valid output rate, cache hit rate, retry count, prompt version, token usage, and estimated cost. These enable the assignment’s cost-tracking bonus and ongoing prompt evaluation.

## 10. Docker strategy

- Use a small, pinned Python base image and a multi-stage build: dependency build stage followed by a minimal runtime stage.
- Run the service as a non-root user.
- Supply configuration through environment variables and an `.env.example`; never build secrets into the image.
- Expose one configurable application port and provide a health endpoint for container orchestration.
- Add a `.dockerignore` to exclude virtual environments, git metadata, secrets, test artifacts, and local caches.
- Provide `docker-compose.yml` for local API execution. Redis can be an optional profile/service for the caching bonus rather than a core dependency.
- Use Uvicorn/Gunicorn worker configuration appropriate to the deployment platform; initial local Docker usage can run a single Uvicorn process.

## 11. Testing strategy

### Unit tests

- Request normalization, individual field limits, and cross-field validation.
- All response-model constraints, score-to-priority reconciliation, and deal-size rules.
- Prompt rendering verifies every normalized field is included correctly, missing fields are explicit, and prompt version is selected.
- PII redaction and cache-key normalization.
- Error mapping, retry eligibility, and cost-estimation calculations.

### Integration tests

- Exercise the FastAPI route with a mocked LLM adapter: happy path, sparse lead, malformed generated JSON, invalid enum, timeout, provider outage, and cache hit.
- Verify the OpenAPI schema and representative request/response examples.
- Run a minimal container smoke test against health and qualification routes once Docker is added.

### Evaluation dataset (bonus)

Create a reviewed, synthetic JSONL dataset covering high-intent decision makers, low-context form submissions, existing customers, ambiguous messages, different company sizes, prompt-injection attempts, and invalid inputs. Expected labels should include score ranges, priority, intent class, and acceptable next-action characteristics.

Evaluation measures:

- JSON/schema-valid output rate
- Priority consistency with score bands
- Agreement with expected score range and intent category
- Unsupported-claim/hallucination rate from manual review
- Recommended-action usefulness
- Latency and estimated cost per lead

Provider calls in ordinary automated tests are mocked. Live-model evaluation is separately gated by credentials and run intentionally, so it cannot make CI flaky or expensive.

## 12. Development phases and approval gates

| Phase | Scope | Completion criteria |
| --- | --- | --- |
| 0 — Contract approval | Confirm technology choice, API enums, score bands, output fields, and privacy assumptions. | This plan is approved. |
| 1 — Foundation | Project configuration, FastAPI app, versioned routing, health endpoint, request IDs, base logs, and standard errors. | App starts; OpenAPI and health routes work. |
| 2 — Contract and validation | Pydantic request/output/error models and deterministic validation rules. | Request and response validation tests pass. |
| 3 — LLM qualification | Provider adapter, prompt registry v1, native structured output, timeout/retry policy, and output guardrails. | Mocked and live opt-in qualification flows return valid results. |
| 4 — Quality and observability | Safe usage/cost tracking, redaction, integration tests, sample payloads, and API documentation. | Required assignment criteria are covered and documented. |
| 5 — Bonus hardening | Cache, evaluation dataset/harness, Docker, Postman collection, and optional Redis compose profile. | Bonus features are independently configurable and tested. |

Each phase should be implemented only after the previous phase is reviewed. Phase 3 will not start until the Phase 2 contract is stable, because prompt schema, output validation, API documentation, and tests all depend on that contract.
