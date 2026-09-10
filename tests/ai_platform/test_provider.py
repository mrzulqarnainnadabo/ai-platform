"""Tests for IModelProvider Abstract Interface Contract and Mock Implementation."""

import asyncio
import unittest
from typing import AsyncGenerator, List, Optional

from ai_platform.core.capabilities import ModelCapabilities, ProviderCapabilities
from ai_platform.core.config import ModelConfig
from ai_platform.core.context import ExecutionContext
from ai_platform.core.messages import Message, Role
from ai_platform.core.provider import IModelProvider
from ai_platform.core.response import FinishReason, ModelResponse, TokenUsage


class MockModelProvider(IModelProvider):
    """Provider-neutral mock provider implementation for kernel testing."""

    @property
    def provider_name(self) -> str:
        return "mock"

    async def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_name="mock",
            supported_models=["mock-model-v1"],
            model_capabilities={"mock-model-v1": ModelCapabilities()},
        )

    async def generate(
        self,
        messages: List[Message],
        config: ModelConfig,
        context: Optional[ExecutionContext] = None,
    ) -> ModelResponse:
        if context and context.cancellation_token.is_cancelled:
            context.cancellation_token.raise_if_cancelled()

        prompt_text = " ".join([m.get_text_content() for m in messages])
        reply = Message(role=Role.ASSISTANT, content=f"Mock response to: {prompt_text}")
        usage = TokenUsage(prompt_tokens=10, completion_tokens=15)

        return ModelResponse(
            message=reply,
            finish_reason=FinishReason.STOP,
            usage=usage,
            model_name=config.model_name,
            provider_name=self.provider_name,
        )

    async def stream(
        self,
        messages: List[Message],
        config: ModelConfig,
        context: Optional[ExecutionContext] = None,
    ) -> AsyncGenerator[ModelResponse, None]:
        chunks = ["Chunk 1", "Chunk 2", "Chunk 3"]
        for i, chunk in enumerate(chunks):
            if context and context.cancellation_token.is_cancelled:
                context.cancellation_token.raise_if_cancelled()

            msg = Message(role=Role.ASSISTANT, content=chunk)
            finish = FinishReason.STOP
            yield ModelResponse(
                message=msg,
                finish_reason=finish,
                usage=TokenUsage(prompt_tokens=5, completion_tokens=2),
                model_name=config.model_name,
                provider_name=self.provider_name,
            )


class TestIModelProviderContract(unittest.TestCase):
    """Tests IModelProvider abstract interface contract compliance."""

    def setUp(self) -> None:
        self.provider = MockModelProvider()

    def test_provider_name_property(self) -> None:
        self.assertEqual(self.provider.provider_name, "mock")

    def test_get_capabilities(self) -> None:
        caps = asyncio.run(self.provider.get_capabilities())
        self.assertEqual(caps.provider_name, "mock")
        self.assertIn("mock-model-v1", caps.supported_models)

    def test_generate(self) -> None:
        messages = [Message(role=Role.USER, content="Hello Mock")]
        config = ModelConfig(model_name="mock-model-v1")
        resp = asyncio.run(self.provider.generate(messages, config))

        self.assertEqual(resp.provider_name, "mock")
        self.assertEqual(resp.model_name, "mock-model-v1")
        self.assertEqual(resp.finish_reason, FinishReason.STOP)
        self.assertIn("Mock response to: Hello Mock", resp.message.get_text_content())

    def test_stream(self) -> None:
        async def run_stream():
            messages = [Message(role=Role.USER, content="Stream Test")]
            config = ModelConfig(model_name="mock-model-v1")
            chunks = []
            async for chunk in self.provider.stream(messages, config):
                chunks.append(chunk.message.get_text_content())
            return chunks

        received = asyncio.run(run_stream())
        self.assertEqual(len(received), 3)
        self.assertEqual(received, ["Chunk 1", "Chunk 2", "Chunk 3"])


if __name__ == "__main__":
    unittest.main()
