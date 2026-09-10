import asyncio
import time
from dataclasses import dataclass, field
from typing import AsyncGenerator, List, Optional
from ai_platform.core.config import ModelConfig
from ai_platform.core.context import ExecutionContext
from ai_platform.core.errors import CancellationError, ProviderError, ProviderTimeoutError, normalize_provider_error
from ai_platform.core.messages import Message
from ai_platform.core.response import ModelResponse
from .registry import ProviderRegistry
from .retry import RetryPolicy


@dataclass(frozen=True)
class RuntimeResult:
    response: ModelResponse
    metadata: dict = field(default_factory=dict)


class ModelRuntime:
    def __init__(self, registry: ProviderRegistry, retry_policy: Optional[RetryPolicy] = None) -> None:
        self.registry = registry
        self.retry_policy = retry_policy or RetryPolicy()

    def _context(self, config: ModelConfig, context: Optional[ExecutionContext]) -> ExecutionContext:
        return context or ExecutionContext(timeout_seconds=config.timeout_seconds)

    async def generate(self, messages: List[Message], config: ModelConfig, provider_name: str, context: Optional[ExecutionContext] = None) -> RuntimeResult:
        ctx = self._context(config, context)
        provider = self.registry.resolve(provider_name)
        started = time.monotonic()
        last_error: Optional[ProviderError] = None
        for attempt in range(self.retry_policy.max_attempts):
            ctx.cancellation_token.raise_if_cancelled()
            try:
                response = await asyncio.wait_for(provider.generate(messages, config, ctx), timeout=ctx.timeout_seconds)
                return RuntimeResult(response, self._meta(ctx, provider_name, config, messages, started, attempt + 1, "success"))
            except asyncio.TimeoutError as exc:
                raise ProviderTimeoutError("Model execution timed out", provider_name=provider_name, model_name=config.model_name) from exc
            except CancellationError:
                raise
            except Exception as exc:
                err = normalize_provider_error(exc, provider_name, config.model_name)
                last_error = err
                if not isinstance(err, self.retry_policy.retryable_errors) or attempt + 1 >= self.retry_policy.max_attempts:
                    raise err
                await asyncio.sleep(self.retry_policy.backoff_seconds * (attempt + 1))
        raise last_error or ProviderError("Model execution failed", provider_name=provider_name, model_name=config.model_name)

    async def stream(self, messages: List[Message], config: ModelConfig, provider_name: str, context: Optional[ExecutionContext] = None) -> AsyncGenerator[RuntimeResult, None]:
        ctx = self._context(config, context)
        provider = self.registry.resolve(provider_name)
        started = time.monotonic()
        deadline = started + ctx.timeout_seconds
        generator = provider.stream(messages, config, ctx)
        try:
            while True:
                ctx.cancellation_token.raise_if_cancelled()
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ProviderTimeoutError("Model stream timed out", provider_name=provider_name, model_name=config.model_name)
                try:
                    chunk = await asyncio.wait_for(generator.__anext__(), timeout=remaining)
                except StopAsyncIteration:
                    break
                except asyncio.TimeoutError as exc:
                    raise ProviderTimeoutError("Model stream timed out", provider_name=provider_name, model_name=config.model_name) from exc
                yield RuntimeResult(chunk, self._meta(ctx, provider_name, config, messages, started, 1, "stream"))
        except CancellationError:
            raise
        except ProviderError:
            raise
        except Exception as exc:
            raise normalize_provider_error(exc, provider_name, config.model_name) from exc
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
