# AI Platform Roadmap

## Phase 0–1.1 — Foundation and repository intelligence
Status: **complete on the current productionization line**

- upstream provenance/licensing
- repository audit and classification
- architecture and governance guardrails
- automated-delivery safety baseline

## Phase 2A–2E — Trusted model foundation
Status: **implemented and consolidated**

- provider-neutral kernel contracts
- deterministic runtime
- timeout/cancellation separation
- provider registry
- mock provider
- OpenAI-compatible provider
- capability/policy/human-approval boundary
- architecture and security tests

## Phase 2F — Application authorization seam
Status: **implemented**

- `AuthorizationContext`
- `AuthContextProvider` application-boundary protocol
- `AuthorizedModelRuntime`
- external consumer integration example

## Phase 3 — Productionization
Status: **foundation implemented; host integration remains**

- safe observability contracts
- liveness/readiness contracts
- validated provider configuration
- bounded retry policy
- CI compile/test/secret gates
- deployment and operations documentation

## Current highest-value work

1. Keep native SSE streaming tested and honest.
2. Integrate real application AuthN/AuthZ at the consumer boundary.
3. Integrate one real consumer (ISEYC Civic Brain or Hubil Firstline) without moving domain logic into the platform kernel.
4. Exercise deployment, health/readiness, and rollback in the consumer host.
5. Add provider adapters only when justified by real consumer requirements.

## Deferred by design

Agent loops, RAG, memory, multi-agent orchestration, workflow engines, and UI are intentionally deferred until the trusted model foundation is proven in a real consumer.

## Production gate

The library itself is not declared a deployed production service. Production readiness requires a real host with authenticated requests, consumer integration, externalized secrets, operational telemetry, health/readiness, reproducible deployment, and a tested rollback procedure.
