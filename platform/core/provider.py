"""IModelProvider Abstract Interface Contract for AI Platform Kernel."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Optional

from platform.core.capabilities import ProviderCapabilities
from platform.core.config import ModelConfig
from platform.core.context import ExecutionContext
from platform.core.messages import Message
from platform.core.response import ModelResponse


class IModelProvider(ABC):
    """Abstract provider-neutral interface contract for LLM model providers.

    All platform model adapters (e.g., OpenAIAdapter, GeminiAdapter, AnthropicAdapter,
    OllamaAdapter) must implement this contract.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier for the provider (e.g., 'openai', 'anthropic', 'gemini')."""
        pass

    @abstractmethod
    async def get_capabilities(self) -> ProviderCapabilities:
        """Returns provider and model capability metadata."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        config: ModelConfig,
        context: Optional[ExecutionContext] = None,
    ) -> ModelResponse:
        """Executes a non-streaming model completion request.

        Args:
            messages: Ordered list of conversation messages.
            config: Provider-neutral model execution parameters.
            context: Optional execution context carrying cancellation tokens & trace IDs.

        Returns:
            ModelResponse containing assistant message, token usage, and finish reason.

        Raises:
            ProviderError: Standardized exception hierarchy on generation failures.
        """
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[Message],
        config: ModelConfig,
        context: Optional[ExecutionContext] = None,
    ) -> AsyncGenerator[ModelResponse, None]:
        """Streams completion tokens and incremental tool call chunks.

        Args:
            messages: Ordered list of conversation messages.
            config: Provider-neutral model execution parameters.
            context: Optional execution context carrying cancellation tokens & trace IDs.

        Yields:
            ModelResponse chunks containing incremental text or tool call fragments.

        Raises:
            ProviderError: Standardized exception hierarchy on streaming failures.
        """
        pass
