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
- Intelligence workspace: `/app/cases`
- Protected intelligence API: `/api/v1/cases`

### Required production environment variables

Set these in the Vercel project settings, never in source control:

- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- `SUPABASE_SERVICE_ROLE_KEY` — server-only key used by the durable intelligence case repository; mark Sensitive in Vercel
- `INTEL_CASE_STORE=supabase` — ensures intelligence cases use durable Supabase storage rather than process-local memory
- One provider credential:
  - `XAI_API_KEY` — recommended for the current xAI/Grok deployment; mark Sensitive in Vercel
  - `OPENAI_API_KEY` — use instead when targeting OpenAI

### Provider configuration

For xAI/Grok:

- `OPENAI_BASE_URL=https://api.x.ai/v1`
- `AI_PLATFORM_PROVIDER=openai-compatible`
- `AI_PLATFORM_DEFAULT_MODEL` is optional; when omitted, the application selects `grok-4.6` for the xAI endpoint
- `AI_PLATFORM_TRIAGE_MODEL` is optional; when omitted, case triage uses the same provider-compatible default model

For OpenAI:

- Omit `OPENAI_BASE_URL` or set `OPENAI_BASE_URL=https://api.openai.com/v1`
- `AI_PLATFORM_PROVIDER=openai-compatible`
- When `AI_PLATFORM_DEFAULT_MODEL` is omitted, the application selects `gpt-4o-mini`

Other optional variables:

- `AI_PLATFORM_PROVIDER_TIMEOUT_SECONDS`
- `AI_PLATFORM_TENANT_CLAIM`
- `AI_PLATFORM_PERMISSIONS_CLAIM`
- `AI_PLATFORM_DEFAULT_MODEL`
- `AI_PLATFORM_TRIAGE_MODEL`

OpenAI and xAI share the same OpenAI-compatible adapter and authorization path. When both provider keys exist, the endpoint determines the preferred credential: `XAI_API_KEY` is preferred for `https://api.x.ai/v1`, and `OPENAI_API_KEY` is preferred for `https://api.openai.com/v1`.

The browser front door receives only `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY`. Provider credentials and `SUPABASE_SERVICE_ROLE_KEY` are never rendered into the browser.

## Configuration

Use environment variables for credentials. Never commit API keys or include them in logs. Local HTTP gateways are permitted only for loopback hosts by the configuration contract.

On Vercel, `INTEL_CASE_STORE=supabase` is required for the intelligence case workspace. The server-side Supabase service key is never a browser credential.

## Health

Hosts should expose liveness independently from model/provider calls. Readiness may include provider connectivity where operationally justified. Health responses must not expose secrets.

## Rollback

Deploy immutable versions and retain the previous known-good version. Prefer Vercel promotion / previous deployment rollback.

## Pre-deployment gate

Run `python -m pytest -q` and `python -m compileall -q ai_platform api`. Validate production configuration, secrets management, policy enforcement, consumer integration, health/readiness, and the host's rollback procedure before deployment.

A successful CI run does not constitute production verification. After a new Vercel deployment is Ready, perform an authenticated HTTP smoke test covering `/app/cases`, case listing/creation/retrieval, triage, evidence attachment, and audit persistence before declaring the intelligence slice production-verified.
