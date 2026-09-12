# AI Platform

**Governed, provider-neutral AI execution infrastructure.**

Authenticated model generation and streaming with deterministic authorization. OpenAI and xAI/Grok share one OpenAI-compatible adapter and the same security path. AI output is never institutional authority.

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
| Generate + SSE stream API | Implemented |
| Browser front door (`/app`) | Implemented (sign-in + chat) |
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

### Environment (server only)

See `.env.example` for a full template. Never commit `.env`.

| Variable | Required | Secret | Purpose |
|----------|----------|--------|---------|
| `SUPABASE_URL` | Yes (host) | Treat as sensitive | Auth project URL |
| `SUPABASE_PUBLISHABLE_KEY` | Yes (host) | Treat as sensitive | JWT verification + browser Auth |
| `OPENAI_API_KEY` or `XAI_API_KEY` | Yes (model calls) | **Yes** | Provider credential |
| `OPENAI_BASE_URL` | No | No | Default OpenAI; set `https://api.x.ai/v1` for Grok |

### Expected HTTP status codes

| Status | Meaning |
|--------|---------|
| 401 | Missing/invalid Bearer token |
| 403 | Authenticated but capability denied (provider **not** called) |
| 400 | Invalid request body |
| 429 | Provider rate limit / quota |
| 503 | Provider not configured |
| 502/504 | Provider failure / timeout |
| 200 | Success |

## Architecture (do not bypass)

```text
Browser /app → Supabase Auth (session)
  → Bearer access token
  → POST /api/v1/models/generate
  → AuthorizationContext (trusted claims only)
  → AuthorizedModelRuntime
  → Provider (OpenAI or xAI)
```

**Must not change without a security review**

- Client-supplied `tenant_id` / permissions are ignored
- `user_metadata` is never an authorization authority
- Signup does not auto-grant model capabilities
- Provider API keys stay server-side only

## Documentation

- [Front door](docs/FRONTDOOR.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Integration](docs/INTEGRATION.md)
- [Supabase auth](docs/SUPABASE_AUTH.md)

## Upstream

Incorporates material from [awesome-llm-apps](https://github.com/shubhamsaboo/awesome-llm-apps) under Apache-2.0. See `UPSTREAM_FOUNDATION.md`.
