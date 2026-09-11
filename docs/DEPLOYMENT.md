# Deployment Contract

`ai-platform` provides a governed FastAPI host at `api/index.py` suitable for Vercel Python runtime, and a provider-neutral library substrate for other hosts.

## Required production path

Application AuthN/AuthZ → `AuthContextProvider` → `AuthorizationContext` → `AuthorizedModelRuntime` → deterministic policy → `ModelRuntime` → `ProviderRegistry` → provider adapter.

## Vercel

The repository is zero-config compatible with Vercel Python runtime:

- Entrypoint: `api/index.py` exporting `app`
- Python: 3.12 (see `.python-version`)
- Public routes: `/api`, `/api/health/live`, `/api/health/ready`
- Protected: `POST /api/v1/models/generate`, `POST /api/v1/models/stream`

Required production environment variables (set in Vercel project settings, never in source):

- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- Provider key (one of):
  - `OPENAI_API_KEY` for OpenAI or any OpenAI-compatible endpoint
  - `XAI_API_KEY` when targeting xAI (also accepted as fallback)
- Optional:
  - `OPENAI_BASE_URL` (default `https://api.openai.com/v1`; set to `https://api.x.ai/v1` for xAI/Grok)
  - `AI_PLATFORM_PROVIDER` (default `openai-compatible`)
  - `AI_PLATFORM_PROVIDER_TIMEOUT_SECONDS`
  - `AI_PLATFORM_TENANT_CLAIM`
  - `AI_PLATFORM_PERMISSIONS_CLAIM`

OpenAI and xAI share the same OpenAI-compatible adapter and the same authorization path.
There is no separate provider auth or policy bypass.

## Configuration

Use environment variables for credentials. Never commit API keys or include them in logs. Local HTTP gateways are permitted only for loopback hosts by the configuration contract.

## Health

Hosts should expose liveness independently from model/provider calls. Readiness may include provider connectivity where operationally justified. Health responses must not expose secrets.

## Rollback

Deploy immutable versions and retain the previous known-good version. Prefer Vercel promotion / previous deployment rollback.

## Pre-deployment gate

Run `python -m pytest -q` and `python -m compileall -q ai_platform api`. Validate production configuration, secrets management, policy enforcement, consumer integration, health/readiness, and the host's rollback procedure before deployment.
