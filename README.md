# AI Platform

A provider-neutral AI platform substrate for reusable, governed AI applications across ISEYC, Hubil, and future products.

## Current foundation

```text
Application AuthN/AuthZ
        ↓
AuthContextProvider (application boundary)
        ↓
AuthorizationContext
        ↓
AuthorizedModelRuntime
        ↓
Deterministic Policy
        ↓
ModelRuntime
        ↓
ProviderRegistry → IModelProvider
        ↓
Mock / OpenAI-Compatible Provider
        ↓
Provider API
```

The kernel and policy layers remain provider-neutral. Provider adapters live outside the kernel. Runtime telemetry is sanitized and excludes prompts, responses, credentials, and authorization headers.

## Safety invariants

- AI output is never authority.
- Policy is deterministic and fail-closed.
- `DENY` and `REQUIRE_HUMAN` cannot execute a provider without the required authorization/approval path.
- Timeout and cancellation are distinct errors.
- Applications should enter through `AuthorizedModelRuntime`, not provider-specific calls.
- No provider credentials are committed to source control.

## Production status

The repository is a **library/substrate, not a deployed HTTP service**. The foundation is suitable for real consumer integration, but production deployment still requires a host application's real AuthN/AuthZ, externalized secrets, operational telemetry, deployment/readiness controls, and a tested rollback procedure.

## Upstream provenance

This repository incorporates material from `Shubhamsaboo/awesome-llm-apps` under Apache-2.0. See `UPSTREAM_FOUNDATION.md` and preserve applicable notices and attribution.

## Engineering rule

**Preserve → understand → test → modularize → consolidate → improve.**

Do not mass-rewrite or mass-delete the upstream foundation. Extract reusable components incrementally after security, licensing, dependencies, and behavior are understood.

## Integration

See `docs/INTEGRATION.md`, `docs/DEPLOYMENT.md`, and `docs/OPERATIONS.md`. The reference consumer is intentionally small and uses the deterministic mock provider.

## Collaboration

Jules, Grok, and ChatGPT operate as complementary engineering/review agents. No agent report alone constitutes a merge or production-release approval.
