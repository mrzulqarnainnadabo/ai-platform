# AI Platform Kernel Core Contracts (`ai_platform.core`)

## Overview

The `ai_platform.core` package establishes the minimal, provider-neutral **Platform Kernel contracts** for the AI Platform.

These contracts define standard data structures, cancellation primitives, exception hierarchies, and abstract provider interfaces (`IModelProvider`) that all model adapters (e.g. OpenAI, Anthropic, Gemini, Ollama) and platform runtime services must implement and consume.

---

## Key Contracts Implemented

1. **`Message` & `Role`** (`ai_platform/core/messages.py`):
   - Provider-neutral message representation supporting `system`, `developer`, `user`, `assistant`, and `tool` roles.
   - Multimodal `ContentPart` support (text, vision/image URLs, audio, base64 binary payloads).
   - Structured `ToolCall` and `ToolResult` attachments.
   - Strict input validation preventing empty/invalid roles or missing content.
   - JSON/dict serialization (`to_dict()`, `from_dict()`, `to_json()`, `from_json()`).

2. **`ModelConfig` & `ResponseFormat`** (`ai_platform/core/config.py`):
   - Model execution parameters: `temperature` (0.0-2.0), `top_p` (0.0-1.0), `max_tokens` (>0), `stop_sequences`, `timeout_seconds` (>0).
   - Non-empty model name validation (`ValueError` raised on empty string).
   - Structured output formatting (`ResponseFormat`: text, JSON object, or JSON schema).
   - Tool definition schemas (`ToolDefinition` & `ToolFunction`).

3. **`ModelResponse` & `TokenUsage`** (`ai_platform/core/response.py`):
   - Standardized completion response containing `Message`, `FinishReason`, `TokenUsage` (`prompt_tokens`, `completion_tokens`, `total_tokens`, `cost_usd`), and structured outputs.
   - Non-negative integer validation for token counts.

4. **`IModelProvider`** (`ai_platform/core/provider.py`):
   - Abstract base class defining `generate()`, `stream()`, and `get_capabilities()`.
   - Strictly provider-agnostic and dependency-light.

5. **Provider Error Hierarchy** (`ai_platform/core/errors.py`):
   - Standardized exceptions: `ProviderError`, `AuthenticationError`, `RateLimitError`, `InvalidRequestError`, `ProviderTimeoutError`, `ProviderQuotaError`, `ProviderUnavailableError`, `ContextWindowExceededError`.
   - Exception normalization utility (`normalize_provider_error`).

6. **`ExecutionContext` & `CancellationToken`** (`ai_platform/core/context.py`):
   - Request tracing, tenant/user isolation IDs, timeout tracking, and cooperative cancellation tokens.

7. **Capability Metadata** (`ai_platform/core/capabilities.py`):
   - Provider capability discovery (`supports_streaming`, `supports_structured_output`, `supports_tools`, `supports_vision`, `max_context_tokens`).

---

## What the Kernel Contracts Deliberately DO NOT Do

To maintain a minimal and trustworthy foundation, `ai_platform.core` explicitly **does not**:
- Depend on provider SDKs (`openai`, `anthropic`, `google-generativeai`, `groq`, `ollama`).
- Depend on orchestration frameworks (`phidata`/`agno`, `langchain`, `crewai`, `pydantic-ai`).
- Perform network requests, file I/O, or database queries.
- Execute shell scripts or arbitrary code.
- Implement domain application logic (e.g. Civic Brain, financial, or legal logic).

---

## How Future Adapters Will Implement Them

In Phase 2D and Phase 3, concrete model adapters in `ai_platform/providers/` (e.g. `OpenAIAdapter`, `GeminiAdapter`) will inherit from `IModelProvider`:

```python
from ai_platform.core import (
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
