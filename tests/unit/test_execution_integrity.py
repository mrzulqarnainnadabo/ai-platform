import asyncio
from pathlib import Path

from ai_platform.core import Message, ModelConfig, Role
from ai_platform.core.response import FinishReason, ModelResponse, TokenUsage
from ai_platform.models.registry import ModelPolicy
from ai_platform.policy.rate_limits import BudgetReservation
from ai_platform.runtime.run_engine import RunEngine
from ai_platform.runtime.model_runtime import RuntimeResult


class RecordingRunStore:
    def __init__(self):
        self.events = []

    def create_run(self, **kwargs):
        self.events.append(("run", kwargs))

    def create_step(self, **kwargs):
        self.events.append(("step", kwargs))

    def create_provider_call(self, **kwargs):
        self.events.append(("provider_call", kwargs))

    def complete(self, **kwargs):
        self.events.append(("complete", kwargs))


class RetryingRateLimits:
    def __init__(self, failures=0):
        self.failures = failures
        self.reservations = []
        self.settlements = []

    def reserve(self, **kwargs):
        self.reservations.append(kwargs)
        return BudgetReservation(
            kwargs["tenant_id"],
            kwargs["subject_id"],
            kwargs["model_id"],
            kwargs["request_id"],
            kwargs["estimated_tokens"],
        )

    def settle(self, reservation, *, actual_tokens):
        self.settlements.append((reservation, actual_tokens))
        if self.failures:
            self.failures -= 1
            raise RuntimeError("simulated settlement transport failure")


class SuccessfulRuntime:
    async def generate(self, *args, **kwargs):
        return RuntimeResult(
            ModelResponse(
                Message(Role.ASSISTANT, "ok"),
                FinishReason.STOP,
                TokenUsage(12, 7, 19),
                "mock",
                "mock",
            ),
            {},
        )

    async def stream(self, *args, **kwargs):
        yield RuntimeResult(
            ModelResponse(
                Message(Role.ASSISTANT, "chunk"),
                FinishReason.STOP,
                TokenUsage(12, 7, 19),
                "mock",
                "mock",
            ),
            {},
        )


class CancellationRuntime:
    async def generate(self, *args, **kwargs):
        raise AssertionError("generate should not be called")

    async def stream(self, *args, **kwargs):
        yield RuntimeResult(
            ModelResponse(
                Message(Role.ASSISTANT, "chunk"),
                FinishReason.NONE,
                TokenUsage(12, 7, 19),
                "mock",
                "mock",
            ),
            {},
        )
        raise asyncio.CancelledError()


def test_generate_retries_settlement_after_transport_failure():
    store = RecordingRunStore()
    limits = RetryingRateLimits(failures=1)
    engine = RunEngine(SuccessfulRuntime(), store, limits)
    policy = ModelPolicy("mock", "mock", "mock", 4096)

    async def run():
        return await engine.generate(
            tenant_id="tenant",
            subject_id="subject",
            model_policy=policy,
            messages=[Message(Role.USER, "hi")],
            config=ModelConfig("mock"),
        )

    result = asyncio.run(run())
    assert result.run_id
    assert [tokens for _, tokens in limits.settlements] == [19, 19]
    assert store.events[-1][1]["status"] == "completed"


def test_stream_retries_settlement_after_transport_failure():
    store = RecordingRunStore()
    limits = RetryingRateLimits(failures=1)
    engine = RunEngine(SuccessfulRuntime(), store, limits)
    policy = ModelPolicy("mock", "mock", "mock", 4096)

    async def run():
        return [
            item
            async for item in engine.stream(
                tenant_id="tenant",
                subject_id="subject",
                model_policy=policy,
                messages=[Message(Role.USER, "hi")],
                config=ModelConfig("mock"),
            )
        ]

    results = asyncio.run(run())
    assert results
    assert [tokens for _, tokens in limits.settlements] == [19, 19]
    assert store.events[-1][1]["status"] == "completed"


def test_cancelled_stream_settles_conservatively_before_propagating_cancellation():
    store = RecordingRunStore()
    limits = RetryingRateLimits()
    engine = RunEngine(CancellationRuntime(), store, limits)
    policy = ModelPolicy("mock", "mock", "mock", 4096)

    async def run():
        with pytest.raises(asyncio.CancelledError):
            async for _ in engine.stream(
                tenant_id="tenant",
                subject_id="subject",
                model_policy=policy,
                messages=[Message(Role.USER, "hi")],
                config=ModelConfig("mock"),
            ):
                pass

    asyncio.run(run())
    assert len(limits.settlements) == 1
    assert limits.settlements[0][1] == limits.reservations[0]["estimated_tokens"]
    assert store.events[-1][1]["status"] == "failed"


def test_run_engine_does_not_depend_on_process_local_settled_flag():
    root = Path(__file__).resolve().parents[2]
    source = (root / "ai_platform" / "runtime" / "run_engine.py").read_text(encoding="utf-8")
    assert "settled = True" not in source
    assert "settled = False" not in source
    assert "status=\"completed\"" in source
    assert "status=\"failed\"" in source
