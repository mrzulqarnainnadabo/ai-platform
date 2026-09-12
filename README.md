# AI Platform

**Governed, provider-neutral AI execution infrastructure.**

Authenticated model generation and streaming with deterministic authorization. OpenAI, xAI/Grok, and local Ollama share the governed runtime path. AI output is never institutional authority.

## Who it is for

- Teams that need **server-side** model calls with real authentication and capability checks
- Products that must keep provider API keys off the client
- Organizations that want fail-closed policy and tenant isolation before any model runs

## What is production-ready

| Surface | Status |
|--------|--------|
| Provider-neutral kernel | Implemented |
| Deterministic policy + capabilities | Implemented |
| Supabase JWT → authorization context | Implemented |
| OpenAI-compatible provider (OpenAI + xAI) | Implemented |
| Ollama provider (local/loopback only) | Implemented |
| Generate + SSE stream API | Implemented |
| Browser front door (`/app`) | Implemented (sign-in + chat) |
| Intelligence case intake + durable Supabase store | Implemented |
| Health / readiness | Implemented |
| Secret scanning + CI | Implemented |

Experimental upstream demos (agents, RAG, voice samples) are **not** part of the production kernel.

## Quick start (library)

```bash
python -m pip install -e ".[dev]" 2>/dev/null || python -m pip install -e .
python -m pip install -r requirements.txt
python -m pytest -q
python examples/reference_consumer.py
```

The reference consumer uses the **mock** provider (no credentials).

## Hosted API (Vercel / FastAPI)

Entry point: `api/index.py` → FastAPI `app` (and optional `handler` for serverless).
Browser app: `api/frontdoor.py` → `/app`.

**Public**

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Human-readable overview |
| GET | `/app` | Browser sign-in + chat (front door) |
| GET | `/docs` | OpenAPI UI |
| GET | `/api` | Machine-readable discovery |
| GET | `/api/health/live` | Liveness |
| GET | `/api/health/ready` | Readiness |

**Protected** (Bearer Supabase access token)

| Method | Path | Capability |
|--------|------|------------|
| POST | `/api/v1/models/generate` | `model.generate` |
| POST | `/api/v1/models/stream` | `model.stream` (SSE) |
| POST | `/api/v1/cases` | `case.create` |
| GET | `/api/v1/cases/{id}` | `case.read` |
| POST | `/api/v1/cases/{id}/triage` | `case.triage` + `model.generate` |
| POST | `/api/v1/cases/{id}/evidence` | `evidence.attach` |

### Environment (server only)

See `.env.example` for a full template. Never commit `.env`.

| Variable | Required | Secret | Purpose |
|----------|----------|--------|---------|
| `SUPABASE_URL` | Yes (host) | Treat as sensitive | Auth project URL and durable case store |
| `SUPABASE_PUBLISHABLE_KEY` | Yes (host) | Treat as sensitive | JWT verification + browser Auth |
| `INTEL_CASE_STORE` | Yes for explicit production config | No | Set `supabase` for durable case storage |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes for durable case storage | **Yes** | Server-only Supabase repository credential |
| `OPENAI_API_KEY` or `XAI_API_KEY` | Yes (cloud model calls) | **Yes** | Provider credential |
| `OPENAI_BASE_URL` | No | No | OpenAI default; set xAI-compatible base URL for Grok |
| `AI_PLATFORM_PROVIDER` | No | No | `openai-compatible` (default) or `ollama` |
| `AI_PLATFORM_TRIAGE_MODEL` | No | No | Server-selected case triage model |

For Vercel Production, use `INTEL_CASE_STORE=supabase`. Ollama is **local only** and loopback-bound (`127.0.0.1:11434`); a Vercel deployment cannot reach Ollama running on your laptop. Use a cloud provider for Vercel Production, or host Ollama where the application can safely reach it.

### Expected HTTP status codes

| Status | Meaning |
|--------|---------|
| 401 | Missing/invalid Bearer token |
| 403 | Authenticated but capability denied (provider **not** called) |
| 400 | Invalid request body |
| 404 | Case not found / not visible to the tenant |
| 429 | Provider rate limit / quota |
| 503 | Provider not configured |
| 502/504 | Provider failure / timeout |
| 200/201 | Success |

## Intelligence case intake

The case-intake vertical slice is a governed durable workflow:

`Problem → Case → Assertions → Missing Evidence → Evidence → Audit`

Production persistence uses `SupabaseCaseRepository` behind `INTEL_CASE_STORE=supabase`, with database integrity hardening from migrations `0003_intelligence_case_tables` and `0004_intelligence_integrity_guards`. Tenant isolation and capability checks remain enforced at the service layer. Model-assisted triage is advisory only; model output cannot establish a `fact` without linked evidence.

See `docs/INTELLIGENCE_CASE_INTAKE.md` for the API contract, security invariants, and exact Vercel Production environment checklist.

## Architecture (do not bypass)

```text
Browser /app → Supabase Auth (session)
  → Bearer access token
  → AuthorizationContext (trusted claims only)
  → AuthorizedModelRuntime
  → Provider (OpenAI / xAI / local Ollama)
```

**Must not change without a security review**

- Client-supplied `tenant_id` / permissions are ignored
- `user_metadata` is never an authorization authority
- Signup does not auto-grant model capabilities
- Provider API keys stay server-side only
- Ollama is loopback-only and is not reachable from a developer laptop when the app is deployed on Vercel

## Documentation

- [Front door](docs/FRONTDOOR.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Integration](docs/INTEGRATION.md)
- [Supabase auth](docs/SUPABASE_AUTH.md)
- [Intelligence case intake](docs/INTELLIGENCE_CASE_INTAKE.md)
- [Model providers](docs/PROVIDERS.md)

## Upstream

Incorporates material from [awesome-llm-apps](https://github.com/shubhamsaboo/awesome-llm-apps) under Apache-2.0. See `UPSTREAM_FOUNDATION.md`.
