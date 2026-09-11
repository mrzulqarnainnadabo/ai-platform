# Operations Runbook

## Safety invariants

- AI output is never authority.
- Policy is deterministic and fail-closed.
- `DENY` and `REQUIRE_HUMAN` do not execute providers without the required external approval.
- Timeout and cancellation are distinct.
- Provider credentials, prompts, and responses are not operational telemetry.

## Troubleshooting

1. Check the host application's liveness/readiness status.
2. Correlate the request with `trace_id`.
3. Inspect only sanitized runtime metadata: provider, model, capability, status, latency, attempts.
4. Classify provider errors before deciding whether to retry.
5. If policy denies execution, investigate authorization context rather than provider health.

## Incident response

Disable or route around a failing provider at the application/provider-registry boundary. Do not weaken policy to restore availability. Roll back the host application to the last known-good immutable version if a deployment caused the incident.
