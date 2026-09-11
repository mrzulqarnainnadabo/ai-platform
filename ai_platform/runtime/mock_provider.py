from typing import AsyncGenerator, List, Optional
from ai_platform.core.capabilities import ModelCapabilities, ProviderCapabilities
from ai_platform.core.config import ModelConfig
from ai_platform.core.context import ExecutionContext
from ai_platform.core.messages import Message, Role
from ai_platform.core.provider import IModelProvider
from ai_platform.core.response import FinishReason, ModelResponse, TokenUsage


class MockModelProvider(IModelProvider):
    provider_name = "mock"

    async def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(provider_name=self.provider_name, supported_models=["mock"], model_capabilities={"mock": ModelCapabilities()})

    async def generate(self, messages: List[Message], config: ModelConfig, context: Optional[ExecutionContext] = None) -> ModelResponse:
        if context:
            context.cancellation_token.raise_if_cancelled()
        return ModelResponse(Message(Role.ASSISTANT, "Mock response"), FinishReason.STOP, TokenUsage(), config.model_name, self.provider_name)

    async def stream(self, messages: List[Message], config: ModelConfig, context: Optional[ExecutionContext] = None) -> AsyncGenerator[ModelResponse, None]:
        if context:
            context.cancellation_token.raise_if_cancelled()
        for text in ("Mock ", "response"):
            if context:
                context.cancellation_token.raise_if_cancelled()
            yield ModelResponse(Message(Role.ASSISTANT, text), FinishReason.STOP, TokenUsage(), config.model_name, self.provider_name)
