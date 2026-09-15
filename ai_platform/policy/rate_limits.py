"""Database-backed request and token budgets."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai_platform.policy.errors import PolicyDeniedError


@dataclass(frozen=True)
class BudgetReservation:
    tenant_id: str
    subject_id: str
    model_id: str
    request_id: str
    reserved_tokens: int


class RateLimitStore:
    def reserve(self, *, tenant_id: str, subject_id: str, model_id: str, requests_per_minute: int,
                tokens_per_day: int, requested_tokens: int, request_id: str) -> BudgetReservation:
        raise NotImplementedError

    def settle(self, reservation: BudgetReservation, *, actual_tokens: int) -> None:
        raise NotImplementedError


class SupabaseRateLimitStore(RateLimitStore):
    def __init__(self, client: Any) -> None: self.client = client

    def reserve(self, *, tenant_id: str, subject_id: str, model_id: str, requests_per_minute: int,
                tokens_per_day: int, requested_tokens: int, request_id: str) -> BudgetReservation:
        result = self.client.rpc("reserve_ai_platform_budget", {
            "p_tenant_id": tenant_id, "p_subject_id": subject_id, "p_model_id": model_id,
            "p_requests_per_minute": requests_per_minute, "p_tokens_per_day": tokens_per_day,
            "p_requested_tokens": requested_tokens, "p_request_id": request_id,
        }).execute()
        rows = getattr(result, "data", None) or []
        row = rows[0] if isinstance(rows, list) and rows else rows
        if not isinstance(row, dict) or not bool(row.get("allowed")):
            raise PolicyDeniedError((row or {}).get("reason", "AI usage budget unavailable or exceeded") if isinstance(row, dict) else "AI usage budget unavailable")
        return BudgetReservation(tenant_id, subject_id, model_id, request_id, requested_tokens)

    def settle(self, reservation: BudgetReservation, *, actual_tokens: int) -> None:
        self.client.rpc("settle_ai_platform_budget", {
            "p_tenant_id": reservation.tenant_id, "p_subject_id": reservation.subject_id,
            "p_model_id": reservation.model_id, "p_request_id": reservation.request_id,
            "p_reserved_tokens": reservation.reserved_tokens, "p_actual_tokens": max(0, int(actual_tokens)),
        }).execute()


class RateLimitPolicy:
    def __init__(self, store: RateLimitStore) -> None: self.store = store

    def reserve(self, *, tenant_id: str, subject_id: str, model_id: str, requests_per_minute: int,
                tokens_per_day: int, estimated_tokens: int, request_id: str) -> BudgetReservation:
        if not tenant_id or not subject_id or not model_id: raise PolicyDeniedError("Usage policy requires tenant, subject and model identities")
        return self.store.reserve(tenant_id=tenant_id, subject_id=subject_id, model_id=model_id,
                                  requests_per_minute=max(1, requests_per_minute), tokens_per_day=max(1, tokens_per_day),
                                  requested_tokens=max(1, estimated_tokens), request_id=request_id)

    def settle(self, reservation: BudgetReservation, *, actual_tokens: int) -> None:
        self.store.settle(reservation, actual_tokens=actual_tokens)
