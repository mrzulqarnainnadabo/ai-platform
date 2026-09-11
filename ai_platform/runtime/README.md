# Runtime

`AuthorizedModelRuntime` is the recommended application entry point. It evaluates deterministic policy before delegating to `ModelRuntime`, which handles timeout, cancellation, bounded retries, and provider resolution.

Applications should not embed provider-specific branching. Register adapters with `ProviderRegistry` and use the normalized `IModelProvider` contract.
