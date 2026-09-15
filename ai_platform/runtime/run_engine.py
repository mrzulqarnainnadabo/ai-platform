"""Durable model execution orchestration.

RunEngine sits immediately before provider execution. It records a run, step,
provider call and cost record in Supabase and settles the usage reservation.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, AsyncGenerator, List, Optional
from uuid import uuid4

from ai_platform.core.config import ModelConfig
from ai_platform.core.context import ExecutionContext
from ai_platform.core.messages import Message
from ai_platform.core.response import ModelResponse
from ai_platform.models.registry import ModelPolicy
from ai_platform.policy.rate_limits import BudgetReservation, RateLimitPolicy
from .model_runtime import ModelRuntime, RuntimeResult


@dataclass(frozen=True)
class RunResult:
    response: ModelResponse
    metadata: dict
    run_id: str


class SupabaseRunStore:
    def __init__(self, client: Any) -> None:
        self.client = client

    def create_run(self, *, run_id: str, tenant_id: str, subject_id: str, model_id: str, provider: str, model: str, trace_id: str) -> None:
        self.client.table("ai_platform_runs").insert({
            "id": run_id, "tenant_id": tenant_id, "subject_id": subject_id,
            "model_id": model_id, "provider": provider, "model": model,
            "trace_id": trace_id, "status": "running",
        }).execute()

    def create_step(self, *, step_id: str, run_id: str, step_type: str, status: str = "running") -> None:
        self.client.table("ai_platform_run_steps").insert({
            "id": step_id, "run_id": run_id, "step_type": step_type, "status": status,
        }).execute()

    def create_provider_call(self, *, call_id: str, run_id: str, step_id: str, provider: str, model: str) -> None:
        self.client.table("ai_platform_provider_calls").insert({
            "id": call_id, "run_id": run_id, "step_id": step_id,
            "provider": provider, "model": model, "status": "running",
        }).execute()

    def complete(self, *, run_id: str, step_id: str, call_id: str, status: str,
                 usage: dict, cost_usd: float, latency_ms: float, error_type: str | None = None) -> None:
        self.client.rpc("complete_ai_platform_run", {
            "p_run_id": run_id, "p_step_id": step_id, "p_call_id": call_id,
            "p_status": status, "p_usage": usage, "p_cost_usd": cost_usd,
            "p_latency_ms": latency_ms, "p_error_type": error_type,
        }).execute()


class RunEngine:
    def __init__(self, runtime: ModelRuntime, store: SupabaseRunStore,
                 rate_limits: RateLimitPolicy | None = None) -> None:
        self.runtime = runtime
        self.store = store
        self.rate_limits = rate_limits

    @staticmethod
    def _estimate_tokens(messages: List[Message], max_tokens: int) -> int:
        chars = sum(len(m.get_text_content()) for m in messages)
        return max(1, min(max_tokens, (chars + 3) // 4 + max_tokens))

    async def generate(self, *, tenant_id: str, subject_id: str, model_policy: ModelPolicy,
                       messages: List[Message], config: ModelConfig,
                       context: Optional[ExecutionContext] = None) -> RunResult:
        ctx = context or ExecutionContext(tenant_id=tenant_id, timeout_seconds=config.timeout_seconds)
        run_id, step_id, call_id = uuid4().hex, uuid4().hex, uuid4().hex
        reservation: BudgetReservation | None = None
        started = time.monotonic()
        self.store.create_run(run_id=run_id, tenant_id=tenant_id, subject_id=subject_id,
                              model_id=model_policy.id, provider=model_policy.provider,
                              model=model_policy.model, trace_id=ctx.trace_id)
        self.store.create_step(step_id=step_id, run_id=run_id, step_type="model")
        self.store.create_provider_call(call_id=call_id, run_id=run_id, step_id=step_id,
                                        provider=model_policy.provider, model=model_policy.model)
        try:
            if self.rate_limits:
                reservation = self.rate_limits.reserve(
                    tenant_id=tenant_id, subject_id=subject_id, model_id=model_policy.id,
                    requests_per_minute=model_policy.requests_per_minute,
                    tokens_per_day=model_policy.tokens_per_day,
                    estimated_tokens=self._estimate_tokens(messages, config.max_tokens or model_policy.max_tokens),
                    request_id=run_id,
                )
            result = await self.runtime.generate(messages, config, model_policy.provider, ctx)
            usage = result.response.usage.to_dict()
            cost = model_policy.estimate_cost(usage["prompt_tokens"], usage["completion_tokens"])
            if reservation and self.rate_limits:
                self.rate_limits.settle(reservation, actual_tokens=usage["total_tokens"])
            self.store.complete(run_id=run_id, step_id=step_id, call_id=call_id, status="completed",
                                usage=usage, cost_usd=cost,
                                latency_ms=round((time.monotonic() - started) * 1000, 2))
            metadata = dict(result.metadata)
            metadata.update({"run_id": run_id, "model_id": model_policy.id, "cost_usd": cost})
            return RunResult(result.response, metadata, run_id)
        except Exception as exc:
            if reservation and self.rate_limits:
                try:
                    self.rate_limits.settle(reservation, actual_tokens=0)
                except Exception:
                    pass
            self.store.complete(run_id=run_id, step_id=step_id, call_id=call_id, status="failed",
                                usage={}, cost_usd=0.0,
                                latency_ms=round((time.monotonic() - started) * 1000, 2),
                                error_type=type(exc).__name__)
            raise

    async def stream(self, *, tenant_id: str, subject_id: str, model_policy: ModelPolicy,
                     messages: List[Message], config: ModelConfig,
                     context: Optional[ExecutionContext] = None) -> AsyncGenerator[RuntimeResult, None]:
        """Stream provider results inside the same durable governance envelope.

        Providers that omit streamed usage are accounted conservatively against
        the reserved estimate and recorded with ``usage_available=False``.
        """
        ctx = context or ExecutionContext(tenant_id=tenant_id, timeout_seconds=config.timeout_seconds)
        run_id, step_id, call_id = uuid4().hex, uuid4().hex, uuid4().hex
        reservation: BudgetReservation | None = None
        settled = False
        started = time.monotonic()
        self.store.create_run(run_id=run_id, tenant_id=tenant_id, subject_id=subject_id,
                              model_id=model_policy.id, provider=model_policy.provider,
                              model=model_policy.model, trace_id=ctx.trace_id)
        self.store.create_step(step_id=step_id, run_id=run_id, step_type="model")
        self.store.create_provider_call(call_id=call_id, run_id=run_id, step_id=step_id,
                                        provider=model_policy.provider, model=model_policy.model)
        usage = None
        try:
            if self.rate_limits:
                reservation = self.rate_limits.reserve(
                    tenant_id=tenant_id, subject_id=subject_id, model_id=model_policy.id,
                    requests_per_minute=model_policy.requests_per_minute,
                    tokens_per_day=model_policy.tokens_per_day,
                    estimated_tokens=self._estimate_tokens(messages, config.max_tokens or model_policy.max_tokens),
                    request_id=run_id,
                )
            async for result in self.runtime.stream(messages, config, model_policy.provider, ctx):
                if result.response.usage.total_tokens > 0:
                    usage = result.response.usage.to_dict()
                metadata = dict(result.metadata)
                metadata.update({"run_id": run_id, "model_id": model_policy.id})
                yield RuntimeResult(result.response, metadata)
            if usage is None:
                # Some providers do not expose usage for streamed responses.
                # Do not claim that consumption was zero; conservatively settle
                # the reservation estimate and explicitly mark usage unknown.
                accounting_tokens = reservation.reserved_tokens if reservation else 0
                usage = {"usage_available": False, "accounting_tokens": accounting_tokens}
            if reservation and self.rate_limits:
                settled = True
                actual_tokens = usage["total_tokens"] if usage.get("usage_available", True) else usage["accounting_tokens"]
                self.rate_limits.settle(reservation, actual_tokens=actual_tokens)
            cost = (model_policy.estimate_cost(usage["prompt_tokens"], usage["completion_tokens"])
                    if usage.get("usage_available", True) else 0.0)
            self.store.complete(run_id=run_id, step_id=step_id, call_id=call_id, status="completed",
                                usage=usage, cost_usd=cost,
                                latency_ms=round((time.monotonic() - started) * 1000, 2))
        except Exception as exc:
            if reservation and self.rate_limits and not settled:
                settled = True
                try:
                    self.rate_limits.settle(reservation, actual_tokens=(usage or {}).get("total_tokens", 0))
                except Exception:
                    pass
            self.store.complete(run_id=run_id, step_id=step_id, call_id=call_id, status="failed",
                                usage={}, cost_usd=0.0,
                                latency_ms=round((time.monotonic() - started) * 1000, 2),
                                error_type=type(exc).__name__)
            raise
