import asyncio
import pytest
from ai_platform.core import CancellationError, ModelConfig, Message, Role, ProviderTimeoutError, CancellationToken
from ai_platform.policy import AuthorizationContext, Identity, Permissions, Capability
from ai_platform.runtime import AuthorizedModelRuntime, ModelRuntime, MockModelProvider, ProviderRegistry
from ai_platform.runtime.run_engine import RunEngine
from ai_platform.models.registry import ModelPolicy
from ai_platform.core.response import FinishReason, ModelResponse, TokenUsage
from ai_platform.runtime.model_runtime import RuntimeResult
from ai_platform.policy.rate_limits import BudgetReservation


class MemoryRunStore:
    def create_run(self, **kwargs): pass
    def create_step(self, **kwargs): pass
    def create_provider_call(self, **kwargs): pass
    def complete(self, **kwargs): pass


class RecordingRunStore(MemoryRunStore):
    def __init__(self): self.events = []
    def create_run(self, **kwargs): self.events.append(("run", kwargs))
    def create_step(self, **kwargs): self.events.append(("step", kwargs))
    def create_provider_call(self, **kwargs): self.events.append(("provider_call", kwargs))
    def complete(self, **kwargs): self.events.append(("complete", kwargs))


class RecordingRateLimits:
    def __init__(self): self.reservations = []; self.settlements = []
    def reserve(self, **kwargs):
        self.reservations.append(kwargs)
        return BudgetReservation(kwargs["tenant_id"], kwargs["subject_id"], kwargs["model_id"], kwargs["request_id"], kwargs["estimated_tokens"])
    def settle(self, reservation, *, actual_tokens): self.settlements.append((reservation, actual_tokens))


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


def test_streaming_usage_and_lifecycle_are_governed_and_settled_once():
    class StreamingRuntime:
        async def stream(self, *args, **kwargs):
            yield RuntimeResult(ModelResponse(Message(Role.ASSISTANT, "chunk"), FinishReason.STOP,
                TokenUsage(12, 7, 19), "mock", "mock"))

    store = RecordingRunStore(); limits = RecordingRateLimits()
    engine = RunEngine(StreamingRuntime(), store, limits)
    policy = ModelPolicy("mock", "mock", "mock", 4096, input_cost_per_million=2.0, output_cost_per_million=3.0)
    config = ModelConfig("mock")

    async def run():
        return [x async for x in engine.stream(tenant_id="tenant", subject_id="subject", model_policy=policy,
                                                messages=[Message(Role.USER, "hi")], config=config)]

    results = asyncio.run(run())
    assert results[0].response.usage.total_tokens == 19
    assert [event[0] for event in store.events] == ["run", "step", "provider_call", "complete"]
    assert len(limits.settlements) == 1
    assert limits.settlements[0][1] == 19
    completion = store.events[-1][1]
    assert completion["usage"]["prompt_tokens"] == 12
    assert completion["usage"]["completion_tokens"] == 7
    assert completion["cost_usd"] > 0


def test_failed_stream_after_usage_chunk_settles_actual_usage_once():
    class FailingRuntime:
        async def stream(self, *args, **kwargs):
            yield RuntimeResult(ModelResponse(Message(Role.ASSISTANT, "partial"), FinishReason.STOP,
                TokenUsage(12, 7, 19), "mock", "mock"))
            raise RuntimeError("stream failed")

    store = RecordingRunStore(); limits = RecordingRateLimits()
    engine = RunEngine(FailingRuntime(), store, limits)
    policy = ModelPolicy("mock", "mock", "mock", 4096)

    async def run():
        return [x async for x in engine.stream(tenant_id="tenant", subject_id="subject", model_policy=policy,
                                                messages=[Message(Role.USER, "hi")], config=ModelConfig("mock"))]

    with pytest.raises(RuntimeError, match="stream failed"):
        asyncio.run(run())
    assert len(limits.settlements) == 1
    assert limits.settlements[0][1] == 19
    assert store.events[-1][1]["status"] == "failed"


def test_failed_stream_before_usage_chunk_settles_reserved_estimate_once():
    class FailingBeforeUsageRuntime:
        async def stream(self, *args, **kwargs):
            yield RuntimeResult(ModelResponse(Message(Role.ASSISTANT, "partial"), FinishReason.STOP,
                TokenUsage(), "mock", "mock"))
            raise RuntimeError("stream failed before usage")

    store = RecordingRunStore(); limits = RecordingRateLimits()
    engine = RunEngine(FailingBeforeUsageRuntime(), store, limits)
    policy = ModelPolicy("mock", "mock", "mock", 4096)

    async def run():
        return [x async for x in engine.stream(tenant_id="tenant", subject_id="subject", model_policy=policy,
                                                messages=[Message(Role.USER, "hi")], config=ModelConfig("mock"))]

    with pytest.raises(RuntimeError, match="before usage"):
        asyncio.run(run())
    reserved = limits.reservations[0]["estimated_tokens"]
    assert len(limits.settlements) == 1
    assert limits.settlements[0][1] == reserved
    assert store.events[-1][1]["status"] == "failed"


def test_streaming_without_provider_usage_settles_reserved_estimate_and_marks_unknown():
    class NoUsageRuntime:
        async def stream(self, *args, **kwargs):
            yield RuntimeResult(ModelResponse(Message(Role.ASSISTANT, "chunk"), FinishReason.STOP,
                TokenUsage(), "mock", "mock"))

    store = RecordingRunStore(); limits = RecordingRateLimits()
    engine = RunEngine(NoUsageRuntime(), store, limits)
    policy = ModelPolicy("mock", "mock", "mock", 4096)

    async def run():
        return [x async for x in engine.stream(tenant_id="tenant", subject_id="subject", model_policy=policy,
                                                messages=[Message(Role.USER, "hi")], config=ModelConfig("mock"))]

    asyncio.run(run())
    reserved = limits.reservations[0]["estimated_tokens"]
    assert limits.settlements[0][1] == reserved
    assert store.events[-1][1]["usage"] == {"usage_available": False, "accounting_tokens": reserved}


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
