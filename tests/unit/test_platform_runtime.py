import asyncio
import pytest
from ai_platform.core import CancellationError, ModelConfig, Message, Role, ProviderTimeoutError
from ai_platform.policy import AuthorizationContext, Identity, Permissions, Capability
from ai_platform.runtime import AuthorizedModelRuntime, ModelRuntime, MockModelProvider, ProviderRegistry


def stack():
    registry = ProviderRegistry(); registry.register(MockModelProvider())
    return AuthorizedModelRuntime(ModelRuntime(registry))


def auth(*caps):
    return AuthorizationContext(Identity("user-1"), Permissions(frozenset(caps)))


@pytest.mark.asyncio
async def test_authorized_generation():
    result = await stack().generate(auth(Capability.MODEL_GENERATE), [Message(Role.USER, "hi")], ModelConfig("mock"), "mock")
    assert result.response.message.content == "Mock response"
    assert result.metadata["capability"] == "model.generate"


@pytest.mark.asyncio
async def test_denied_generation_never_calls_provider():
    class Counting(MockModelProvider):
        calls = 0
        async def generate(self, *args, **kwargs):
            self.calls += 1
            return await super().generate(*args, **kwargs)
    provider = Counting(); registry = ProviderRegistry(); registry.register(provider)
    runtime = AuthorizedModelRuntime(ModelRuntime(registry))
    with pytest.raises(Exception) as exc:
        await runtime.generate(auth(), [Message(Role.USER, "hi")], ModelConfig("mock"), "mock")
    assert "denied" in str(exc.value).lower()
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_cancellation_is_distinct():
    token = __import__("ai_platform.core", fromlist=["CancellationToken"]).CancellationToken(); token.cancel("user stopped")
    with pytest.raises(CancellationError): token.raise_if_cancelled()
    assert not issubclass(CancellationError, ProviderTimeoutError)
