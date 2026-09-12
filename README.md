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

**Public**

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Human-readable overview |
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
| `SUPABASE_PUBLISHABLE_KEY` | Yes (host) | Treat as sensitive | JWT verification |
| `OPENAI_API_KEY` or `XAI_API_KEY` | Yes (model calls) | **Yes** | Provider credential |
| `OPENAI_BASE_URL` | No | No | Default OpenAI; set `https://api.x.ai/v1` for Grok |
| `AI_PLATFORM_PROVIDER` | No | No | Default `openai-compatible` |
| `AI_PLATFORM_TENANT_CLAIM` | No | No | Default `ai_platform_tenant_id` |
| `AI_PLATFORM_PERMISSIONS_CLAIM` | No | No | Default `ai_platform_permissions` |

### Example authenticated request

```bash
export BASE=https://your-deployment.vercel.app
export SUPABASE_ACCESS_TOKEN=...   # from Supabase Auth; not a provider key

curl -s -X POST "$BASE/api/v1/models/generate" \
  -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model_name":"gpt-4o-mini","messages":[{"role":"user","content":"Hello"}]}'
```

### Expected HTTP status codes

| Status | Meaning |
|--------|---------|
| 401 | Missing/invalid Bearer token |
| 403 | Authenticated but capability denied (provider **not** called) |
| 400 | Invalid request body |
| 429 | Provider rate limit / quota |
| 503 | Provider not configured |
| 502/504 | Provider failure / timeout |
| 200 | Success (generate JSON or SSE stream) |

## Architecture (do not bypass)

```text
Client
  → Vercel / FastAPI (api/)
  → Supabase JWT verification (integrations/)
  → AuthorizationContext (tenant + capabilities from trusted claims only)
  → AuthorizedModelRuntime   ← application entry for model work
  → ModelRuntime
  → ProviderRegistry
  → OpenAI-compatible adapter (OpenAI or xAI)
  → Normalized response
```

**Must not change without a security review**

- Client-supplied `tenant_id` / permissions are ignored
- `user_metadata` is never an authorization authority
- `DENY` / missing capability must not reach a provider
- Provider API keys stay server-side only
- Prompts, responses, and credentials are not operational logs

## Adding a provider

1. Implement `IModelProvider` (`generate`, `stream`, capabilities).
2. Map vendor errors to `ai_platform.core.errors`.
3. Register on `ProviderRegistry` in the **host** (not in core).
4. Keep OpenAI-wire vendors on the existing OpenAI-compatible adapter when possible.

## Documentation

- [Deployment](docs/DEPLOYMENT.md)
- [Integration](docs/INTEGRATION.md)
- [Operations](docs/OPERATIONS.md)
- [Supabase auth](docs/SUPABASE_AUTH.md)
- [Architecture](PLATFORM_ARCHITECTURE.md)
- [Governance](PLATFORM_GOVERNANCE.md)

## Upstream

Incorporates material from [awesome-llm-apps](https://github.com/shubhamsaboo/awesome-llm-apps) under Apache-2.0. See `UPSTREAM_FOUNDATION.md`.

## Engineering rule

Preserve → understand → test → modularize → consolidate → improve.
