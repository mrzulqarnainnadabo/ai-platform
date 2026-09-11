# Consumer Integration

The platform is a substrate. Applications own authentication, domain rules, HTTP/API boundaries, and user-facing workflows.

## Recommended request path

1. Application authenticates the user/session.
2. Application maps trusted claims to `AuthorizationContext` through `AuthContextProvider`.
3. Application requests a platform capability.
4. `AuthorizedModelRuntime` evaluates deterministic policy.
5. Allowed requests execute through `ModelRuntime` and `ProviderRegistry`.
6. The application receives a normalized `RuntimeResult`.

Do not place ISEYC, Hubil, political, financial, health, or other domain-specific rules in `ai_platform.core` or `ai_platform.policy`.

The reference implementation in `examples/reference_consumer.py` uses the mock provider and requires no credentials. Replace the application-boundary identity provider and register the required real provider in a host service for production use.
