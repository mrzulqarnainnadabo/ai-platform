"""Database-backed request and token budgets.

The policy is deliberately fail-closed: if the counter store cannot atomically
reserve capacity, provider execution is denied rather than bypassing the budget.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai_platform.core.errors import PolicyError
from ai_platform.policy.errors import PolicyDeniedError


@dataclass(frozen=True)
class BudgetReservation:
    tenant_id: str
    subject_id: str
    model_id: str
    request_id: str
    reserved_tokens: int


class RateLimitStore:
    """Protocol-like base for an atomic Supabase/Postgres counter store."""

    def reserve(self, *, tenant_id: str, subject_id: str, model_id: str,
                requests_per_minute: int, tokens_per_day: int,
                requested_tokens: int, request_id: str) -> BudgetReservation:
        raise NotImplementedError

    def settle(self, reservation: BudgetReservation, *, actual_tokens: int) -> None:
        raise NotImplementedError


class SupabaseRateLimitStore(RateLimitStore):
    def __init__(self, client: Any) -> None:
        self.client = client

    def reserve(self, *, tenant_id: str, subject_id: str, model_id: str,
                requests_per_minute: int, tokens_per_day: int,
                requested_tokens: int, request_id: str) -> BudgetReservation:
        result = self.client.rpc(
            "reserve_ai_platform_budget",
            {
                "p_tenant_id": tenant_id,
                "p_subject_id": subject_id,
                "p_model_id": model_id,
                "p_requests_per_minute": requests_per_minute,
                "p_tokens_per_day": tokens_per_day,
                "p_requested_tokens": requested_tokens,
                "p_request_id": request_id,
            },
        ).execute()
        rows = getattr(result, "data", None) or []
        row = rows[0] if isinstance(rows, list) and rows else rows
        if not isinstance(row, dict):
            raise PolicyError("Budget reservation returned an invalid database response")
        if not bool(row.get("allowed")):
            raise PolicyDeniedError(str(row.get("reason") or "AI usage budget exceeded"))
        return BudgetReservation(tenant_id, subject_id, model_id, request_id, requested_tokens)

    def settle(self, reservation: BudgetReservation, *, actual_tokens: int) -> None:
        self.client.rpc(
            "settle_ai_platform_budget",
            {
                "p_tenant_id": reservation.tenant_id,
                "p_subject_id": reservation.subject_id,
                "p_model_id": reservation.model_id,
                "p_request_id": reservation.request_id,
                "p_reserved_tokens": reservation.reserved_tokens,
                "p_actual_tokens": max(0, int(actual_tokens)),
            },
        ).execute()


class RateLimitPolicy:
    """Enforce request/minute and token/day budgets before provider execution."""

    def __init__(self, store: RateLimitStore) -> None:
        self.store = store

    def reserve(self, *, tenant_id: str, subject_id: str, model_id: str,
                requests_per_minute: int, tokens_per_day: int,
                estimated_tokens: int, request_id: str) -> BudgetReservation:
        if not tenant_id or not subject_id or not model_id:
            raise PolicyDeniedError("Usage policy requires tenant, subject and model identities")
        if estimated_tokens <= 0:
            estimated_tokens = 1
        return self.store.reserve(
            tenant_id=tenant_id,
            subject_id=subject_id,
            model_id=model_id,
            requests_per_minute=max(1, requests_per_minute),
            tokens_per_day=max(1, tokens_per_day),
            requested_tokens=estimated_tokens,
            request_id=request_id,
        )

    def settle(self, reservation: BudgetReservation, *, actual_tokens: int) -> None:
        self.store.settle(reservation, actual_tokens=actual_tokens)
