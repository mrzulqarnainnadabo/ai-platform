# AI Platform Kernel Core Contracts (`platform/core`)

## Overview

The `platform/core` package establishes the minimal, provider-neutral **Platform Kernel contracts** for the AI Platform.

These contracts define standard data structures, cancellation primitives, exception hierarchies, and abstract provider interfaces (`IModelProvider`) that all model adapters (e.g. OpenAI, Anthropic, Gemini, Ollama) and platform runtime services must implement and consume.

---

## Key Contracts Implemented

1. **`Message` & `Role`** (`platform/core/messages.py`):
   - Provider-neutral message representation supporting `system`, `developer`, `user`, `assistant`, and `tool` roles.
   - Multimodal `ContentPart` support (text, vision/image URLs, audio).
   - Structured `ToolCall` and `ToolResult` attachments.
   - JSON/dict serialization (`to_dict()`, `from_dict()`, `to_json()`, `from_json()`).

2. **`ModelConfig` & `ResponseFormat`** (`platform/core/config.py`):
   - Model execution parameters: `temperature`, `top_p`, `max_tokens`, `stop_sequences`, `timeout_seconds`.
   - Structured output formatting (`ResponseFormat`: text, JSON object, or JSON schema).
   - Tool definition schemas (`ToolDefinition` & `ToolFunction`).

3. **`ModelResponse` & `TokenUsage`** (`platform/core/response.py`):
   - Standardized completion response containing `Message`, `FinishReason`, `TokenUsage` (`prompt_tokens`, `completion_tokens`, `total_tokens`, `cost_usd`), and structured outputs.

4. **`IModelProvider`** (`platform/core/provider.py`):
   - Abstract base class defining `generate()`, `stream()`, and `get_capabilities()`.
   - Strictly provider-agnostic and dependency-light.

5. **Provider Error Hierarchy** (`platform/core/errors.py`):
   - Standardized exceptions: `ProviderError`, `AuthenticationError`, `RateLimitError`, `InvalidRequestError`, `ProviderTimeoutError`, `ProviderQuotaError`, `ProviderUnavailableError`, `ContextWindowExceededError`.
   - Exception normalization utility (`normalize_provider_error`).

6. **`ExecutionContext` & `CancellationToken`** (`platform/core/context.py`):
   - Request tracing, tenant/user isolation IDs, timeout tracking, and cooperative cancellation tokens.

7. **Capability Metadata** (`platform/core/capabilities.py`):
   - Provider capability discovery (`supports_streaming`, `supports_structured_output`, `supports_tools`, `supports_vision`, `max_context_tokens`).

---

## What the Kernel Contracts Deliberately DO NOT Do

To maintain a minimal and trustworthy foundation, `platform/core` explicitly **does not**:
- Depend on provider SDKs (`openai`, `anthropic`, `google-generativeai`, `groq`, `ollama`).
- Depend on orchestration frameworks (`phidata`/`agno`, `langchain`, `crewai`, `pydantic-ai`).
- Perform network requests, file I/O, or database queries.
- Execute shell scripts or arbitrary code.
- Implement domain application logic (e.g. Civic Brain, financial, or legal logic).

---

## How Future Adapters Will Implement Them

In Phase 2D and Phase 3, concrete model adapters in `platform/providers/` (e.g. `OpenAIAdapter`, `GeminiAdapter`) will inherit from `IModelProvider`:

```python
from platform.core import (
    IModelProvider, Message, ModelConfig, ModelResponse,
    ProviderCapabilities, ExecutionContext
)

class OpenAIAdapter(IModelProvider):
    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate(self, messages: list[Message], config: ModelConfig, context: ExecutionContext = None) -> ModelResponse:
        # Translates platform Message -> OpenAI SDK payload -> platform ModelResponse
        ...
```

---

## How Future Applications Will Consume Them

Platform runtime services and applications (such as ISEYC Civic Brain) will consume `IModelProvider` rather than coupling directly to LLM vendor SDKs:

```python
async def run_agent(provider: IModelProvider, messages: list[Message], config: ModelConfig):
    response = await provider.generate(messages, config)
    print(f"Assistant response: {response.message.get_text_content()}")
```
