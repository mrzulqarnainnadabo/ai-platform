# Provider Adapters

Provider adapters implement `IModelProvider` and live outside the kernel/runtime/policy packages.

`OpenAICompatibleProvider` uses Python stdlib HTTP/SSE and supports OpenAI-compatible gateways. Credentials come from the constructor or `OPENAI_API_KEY`; base URL may be supplied through the constructor or `OPENAI_BASE_URL`.

Streaming is native SSE. The runtime remains responsible for the overall deadline and cooperative cancellation.
