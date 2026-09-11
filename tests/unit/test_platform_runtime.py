import asyncio
import pytest
from ai_platform.core import CancellationError, ModelConfig, Message, Role, ProviderTimeoutError, CancellationToken
from ai_platform.policy import AuthorizationContext, Identity, Permissions, Capability
from ai_platform.runtime import AuthorizedModelRuntime, ModelRuntime, MockModelProvider, ProviderRegistry


def stack(provider=None):
    registry = ProviderRegistry(); registry.register(provider or MockModelProvider())
    return AuthorizedModelRuntime(ModelRuntime(registry))


def auth(*caps):
    return AuthorizationContext(Identity("user-1"), Permissions(frozenset(caps)))


def test_authorized_generation():
    async def run():
        return await stack().generate(auth(Capability.MODEL_GENERATE), [Message(Role.USER, "hi")], ModelConfig("mock"), "mock")
    result = asyncio.run(run())
    assert result.response.message.content == "Mock response"
    assert result.metadata["capability"] == "model.generate"


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
