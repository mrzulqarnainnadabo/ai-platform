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

Experimental upstream demos (agents, RAG, voice samples) are **not** part of the production kernel and remain classified separately.

## Quick start (library)

```bash
python -m pip install -e .
python -m pytest -q
```

Reference consumer (mock provider, no credentials):

```bash
python examples/reference_consumer.py
```

## Hosted API (Vercel)

Public:

- `GET /` — human-readable overview
- `GET /docs` — OpenAPI interactive docs
- `GET /api` — machine-readable discovery
- `GET /api/health/live` · `GET /api/health/ready`

Protected (Bearer Supabase JWT required):

- `POST /api/v1/models/generate`
- `POST /api/v1/models/stream`

### Environment (server only)

| Variable | Purpose |
|----------|---------|
| `SUPABASE_URL` | Auth project URL |
| `SUPABASE_PUBLISHABLE_KEY` | Publishable key for JWT verification |
| `OPENAI_API_KEY` or `XAI_API_KEY` | Provider credential |
| `OPENAI_BASE_URL` | Default `https://api.openai.com/v1`; use `https://api.x.ai/v1` for Grok |

Never put provider keys in frontend code or client bundles.

### Example authenticated request

```bash
curl -s -X POST "$BASE/api/v1/models/generate" \
  -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model_name":"gpt-4o-mini","messages":[{"role":"user","content":"Hello"}]}'
```

Unauthorized calls receive **401**. Missing capability receives **403** and the provider is never contacted.

## Architecture

```text
Client
  → Vercel / FastAPI
  → Supabase JWT verification
  → AuthorizationContext (tenant + capabilities from trusted claims only)
  → Deterministic policy
  → AuthorizedModelRuntime
  → ProviderRegistry
  → OpenAI-compatible adapter (OpenAI or xAI)
  → Normalized response
```

Client-supplied `tenant_id` or `permissions` fields are ignored.

## Safety invariants

- AI output is never authority
- Policy is fail-closed
- `DENY` never reaches a provider
- Timeout and cancellation are distinct
- Prompts, responses, and credentials are not operational telemetry

## Documentation

- [Deployment](docs/DEPLOYMENT.md)
- [Integration](docs/INTEGRATION.md)
- [Operations](docs/OPERATIONS.md)
- [Supabase auth](docs/SUPABASE_AUTH.md)
- [Architecture](PLATFORM_ARCHITECTURE.md)
- [Governance](PLATFORM_GOVERNANCE.md)
- [Roadmap](docs/ROADMAP.md)

## Upstream

Incorporates material from [awesome-llm-apps](https://github.com/shubhamsaboo/awesome-llm-apps) under Apache-2.0. See `UPSTREAM_FOUNDATION.md`.

## Engineering rule

Preserve → understand → test → modularize → consolidate → improve.
