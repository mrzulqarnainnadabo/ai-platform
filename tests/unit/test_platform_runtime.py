import asyncio
import pytest
from ai_platform.core import CancellationError, ModelConfig, Message, Role, ProviderTimeoutError, CancellationToken
from ai_platform.policy import AuthorizationContext, Identity, Permissions, Capability
from ai_platform.runtime import AuthorizedModelRuntime, ModelRuntime, MockModelProvider, ProviderRegistry
from ai_platform.runtime.run_engine import RunEngine
from ai_platform.models.registry import ModelPolicy


class MemoryRunStore:
    def create_run(self, **kwargs): pass
    def create_step(self, **kwargs): pass
    def create_provider_call(self, **kwargs): pass
    def complete(self, **kwargs): pass


def stack(provider=None):
    registry = ProviderRegistry(); registry.register(provider or MockModelProvider())
    model_runtime = ModelRuntime(registry)
    return AuthorizedModelRuntime(model_runtime, run_engine=RunEngine(model_runtime, MemoryRunStore()))


def auth(*caps):
    return AuthorizationContext(Identity("user-1"), Permissions(frozenset(caps)))


def test_authorized_generation():
    async def run():
        config = ModelConfig("mock")
        setattr(config, "_model_policy", ModelPolicy("mock", "mock", "mock", 4096))
        return await stack().generate(auth(Capability.MODEL_GENERATE), [Message(Role.USER, "hi")], config, "mock")
    result = asyncio.run(run())
    assert result.response.message.content == "Mock response"
    assert result.metadata["capability"] == "model.generate"


def test_generation_fails_closed_without_governance_engine():
    config = ModelConfig("mock")
    setattr(config, "_model_policy", ModelPolicy("mock", "mock", "mock", 4096))
    runtime = AuthorizedModelRuntime(ModelRuntime(ProviderRegistry()))

    async def run():
        await runtime.generate(auth(Capability.MODEL_GENERATE), [Message(Role.USER, "hi")], config, "mock")

    with pytest.raises(RuntimeError, match="Governance runtime is not configured"):
        asyncio.run(run())


def test_authorized_streaming_uses_governed_run_engine():
    config = ModelConfig("mock")
    setattr(config, "_model_policy", ModelPolicy("mock", "mock", "mock", 4096))

    async def run():
        return [result async for result in stack().stream(
            auth(Capability.MODEL_STREAM), [Message(Role.USER, "hi")], config, "mock")]

    results = asyncio.run(run())
    assert results
    assert results[0].metadata["model_id"] == "mock"
    assert results[0].metadata["run_id"]


def test_denied_generation_never_calls_provider():
    class Counting(MockModelProvider):
        calls = 0
        async def generate(self, *args, **kwargs):
            self.calls += 1
            return await super().generate(*args, **kwargs)
    provider = Counting(); runtime = stack(provider)
    async def run():
        await runtime.generate(auth(), [Message(Role.USER, "hi")], ModelConfig("mock"), "mock")
    with pytest.raises(Exception) as exc:
        asyncio.run(run())
    assert "not granted" in str(exc.value).lower()
    assert provider.calls == 0


def test_cancellation_is_distinct():
    token = CancellationToken(); token.cancel("user stopped")
    with pytest.raises(CancellationError): token.raise_if_cancelled()
    assert not issubclass(CancellationError, ProviderTimeoutError)
