import asyncio
import time
from dataclasses import dataclass, field
from typing import AsyncGenerator, List, Optional
from ai_platform.core.config import ModelConfig
from ai_platform.core.context import ExecutionContext
from ai_platform.core.errors import CancellationError, ProviderError, ProviderTimeoutError, normalize_provider_error
from ai_platform.core.messages import Message
from ai_platform.core.response import ModelResponse
from ai_platform.observability import EventSink, RuntimeEvent
from .registry import ProviderRegistry
from .retry import RetryPolicy


@dataclass(frozen=True)
class RuntimeResult:
    response: ModelResponse
    metadata: dict = field(default_factory=dict)


class ModelRuntime:
    def __init__(self, registry: ProviderRegistry, retry_policy: Optional[RetryPolicy] = None, event_sink: Optional[EventSink] = None) -> None:
        self.registry = registry
        self.retry_policy = retry_policy or RetryPolicy()
        self.event_sink = event_sink

    def _context(self, config: ModelConfig, context: Optional[ExecutionContext]) -> ExecutionContext:
        return context or ExecutionContext(timeout_seconds=config.timeout_seconds)

    def _emit(self, event_type: str, metadata: dict, ctx: ExecutionContext) -> None:
        if self.event_sink:
            self.event_sink.emit(RuntimeEvent(event_type, ctx.trace_id, metadata))

    async def generate(self, messages: List[Message], config: ModelConfig, provider_name: str, context: Optional[ExecutionContext] = None) -> RuntimeResult:
        ctx = self._context(config, context)
        provider = self.registry.resolve(provider_name)
        started = time.monotonic()
        deadline = started + ctx.timeout_seconds
        self._emit("model.generate.started", {"provider_name": provider_name, "model_name": config.model_name, "capability": "model.generate", "message_count": len(messages)}, ctx)
        last_error: Optional[ProviderError] = None
        for attempt in range(self.retry_policy.max_attempts):
            ctx.cancellation_token.raise_if_cancelled()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ProviderTimeoutError("Model execution timed out", provider_name=provider_name, model_name=config.model_name)
            try:
                response = await asyncio.wait_for(provider.generate(messages, config, ctx), timeout=remaining)
                metadata = self._meta(ctx, provider_name, config, messages, started, attempt + 1, "success")
                self._emit("model.generate.completed", metadata, ctx)
                return RuntimeResult(response, metadata)
            except asyncio.TimeoutError as exc:
                error = ProviderTimeoutError("Model execution timed out", provider_name=provider_name, model_name=config.model_name)
                self._emit("model.generate.failed", {"provider_name": provider_name, "model_name": config.model_name, "error_type": type(error).__name__}, ctx)
                raise error from exc
            except CancellationError:
                self._emit("model.generate.cancelled", {"provider_name": provider_name, "model_name": config.model_name, "error_type": "CancellationError"}, ctx)
                raise
            except Exception as exc:
                err = normalize_provider_error(exc, provider_name, config.model_name)
                last_error = err
                if not isinstance(err, self.retry_policy.retryable_errors) or attempt + 1 >= self.retry_policy.max_attempts:
                    self._emit("model.generate.failed", {"provider_name": provider_name, "model_name": config.model_name, "error_type": type(err).__name__}, ctx)
                    raise err
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ProviderTimeoutError("Model execution timed out", provider_name=provider_name, model_name=config.model_name) from err
                await asyncio.sleep(min(self.retry_policy.backoff_seconds * (attempt + 1), remaining))
        raise last_error or ProviderError("Model execution failed", provider_name=provider_name, model_name=config.model_name)

    async def stream(self, messages: List[Message], config: ModelConfig, provider_name: str, context: Optional[ExecutionContext] = None) -> AsyncGenerator[RuntimeResult, None]:
        ctx = self._context(config, context)
        provider = self.registry.resolve(provider_name)
        started = time.monotonic()
        deadline = started + ctx.timeout_seconds
        generator = provider.stream(messages, config, ctx)
        self._emit("model.stream.started", {"provider_name": provider_name, "model_name": config.model_name, "capability": "model.stream", "message_count": len(messages)}, ctx)
        try:
            while True:
                ctx.cancellation_token.raise_if_cancelled()
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ProviderTimeoutError("Model stream timed out", provider_name=provider_name, model_name=config.model_name)
                try:
                    chunk = await asyncio.wait_for(generator.__anext__(), timeout=remaining)
                except StopAsyncIteration:
                    self._emit("model.stream.completed", self._meta(ctx, provider_name, config, messages, started, 1, "stream"), ctx)
                    break
                except asyncio.TimeoutError as exc:
                    raise ProviderTimeoutError("Model stream timed out", provider_name=provider_name, model_name=config.model_name) from exc
                yield RuntimeResult(chunk, self._meta(ctx, provider_name, config, messages, started, 1, "stream"))
        except CancellationError:
            self._emit("model.stream.cancelled", {"provider_name": provider_name, "model_name": config.model_name, "error_type": "CancellationError"}, ctx)
            raise
        except ProviderError as exc:
            self._emit("model.stream.failed", {"provider_name": provider_name, "model_name": config.model_name, "error_type": type(exc).__name__}, ctx)
            raise
        except Exception as exc:
            err = normalize_provider_error(exc, provider_name, config.model_name)
            self._emit("model.stream.failed", {"provider_name": provider_name, "model_name": config.model_name, "error_type": type(err).__name__}, ctx)
            raise err from exc
        finally:
            aclose = getattr(generator, "aclose", None)
            if aclose:
                try:
                    await aclose()
                except Exception:
                    pass

    @staticmethod
    def _meta(ctx: ExecutionContext, provider_name: str, config: ModelConfig, messages: List[Message], started: float, attempts: int, status: str) -> dict:
        return {"trace_id": ctx.trace_id, "provider_name": provider_name, "model_name": config.model_name,
                "capability": "model.stream" if status == "stream" else "model.generate",
                "message_count": len(messages), "latency_ms": round((time.monotonic() - started) * 1000, 2),
                "status": status, "attempts": attempts}
