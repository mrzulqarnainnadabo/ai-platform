import asyncio
import pytest
from ai_platform.core import ModelConfig, Message, Role, ProviderTimeoutError, CancellationError, CancellationToken
from ai_platform.runtime import ModelRuntime, MockModelProvider, ProviderRegistry


class SlowProvider(MockModelProvider):
    async def generate(self, messages, config, context=None):
        await asyncio.sleep(0.05)
        return await super().generate(messages, config, context)


class CancelAwareProvider(MockModelProvider):
    async def generate(self, messages, config, context=None):
        if context:
            context.cancellation_token.raise_if_cancelled()
        await asyncio.sleep(0)
        if context:
            context.cancellation_token.raise_if_cancelled()
        return await super().generate(messages, config, context)


def test_runtime_enforces_wall_clock_timeout():
    registry = ProviderRegistry(); registry.register(SlowProvider())
    runtime = ModelRuntime(registry)
    async def run():
        await runtime.generate([Message(Role.USER, "x")], ModelConfig("mock", timeout_seconds=0.01), "mock")
    with pytest.raises(ProviderTimeoutError): asyncio.run(run())


def test_runtime_preserves_explicit_cancellation():
    token = CancellationToken(); token.cancel("user stopped")
    registry = ProviderRegistry(); registry.register(CancelAwareProvider())
    runtime = ModelRuntime(registry)
    async def run():
        from ai_platform.core import ExecutionContext
        await runtime.generate([Message(Role.USER, "x")], ModelConfig("mock"), "mock", ExecutionContext(cancellation_token=token))
    with pytest.raises(CancellationError): asyncio.run(run())
