# Deployment Contract

`ai-platform` is a library/substrate, not a hosted HTTP service. Production applications host it inside their own service boundary.

## Required production path

Application AuthN/AuthZ → `AuthContextProvider` → `AuthorizationContext` → `AuthorizedModelRuntime` → deterministic policy → `ModelRuntime` → `ProviderRegistry` → provider adapter.

## Configuration

Use environment variables for credentials. Never commit API keys or include them in logs. `OPENAI_API_KEY` and `OPENAI_BASE_URL` are consumed by the OpenAI-compatible adapter; local HTTP gateways are permitted only for loopback hosts by the configuration contract.

## Health

Hosts should expose liveness independently from model/provider calls. Readiness may include provider connectivity where operationally justified. Health responses must not expose secrets.

## Rollback

The host application must deploy immutable versions and retain the previous known-good version. Rollback is a deployment-platform concern and is not claimed as exercised by this library repository until a real host integration exists.

## Pre-deployment gate

Run `python -m pytest -q` and `python -m compileall -q ai_platform`. Validate production configuration, secrets management, policy enforcement, consumer integration, health/readiness, and the host's rollback procedure before deployment.
