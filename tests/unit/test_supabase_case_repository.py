"""Unit tests for SupabaseCaseRepository using a fake client (no network)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import pytest

from ai_platform.intelligence.models import (
    AssertionKind,
    AuditEvent,
    EvidenceSourceType,
    new_assertion,
    new_case,
    new_evidence,
)
from ai_platform.intelligence.repository import InMemoryCaseRepository
from ai_platform.intelligence.service import CaseService
from ai_platform.intelligence.store import (
    CaseStoreConfigurationError,
    get_case_repository,
    reset_case_repository_cache,
)
from ai_platform.intelligence.supabase_repository import SupabaseCaseRepository
from ai_platform.policy.authorization import AuthorizationContext, Identity, Permissions
from ai_platform.policy.capabilities import Capability
from ai_platform.policy.errors import PolicyDeniedError


@dataclass
class _Result:
    data: list[dict[str, Any]] = field(default_factory=list)


class FakeTable:
    def __init__(self, db: dict[str, list[dict]], name: str) -> None:
        self.db = db
        self.name = name
        self._filters: list[tuple[str, Any]] = []
        self._payload: dict | None = None
        self._op = "select"
        self._limit: int | None = None

    def select(self, *_args: str) -> "FakeTable":
        self._op = "select"
        return self

    def eq(self, key: str, value: Any) -> "FakeTable":
        self._filters.append((key, value))
        return self

    def limit(self, n: int) -> "FakeTable":
        self._limit = n
        return self

    def upsert(self, payload: dict) -> "FakeTable":
        self._op = "upsert"
        self._payload = payload
        return self

    def insert(self, payload: dict) -> "FakeTable":
        self._op = "insert"
        self._payload = payload
        return self

    def execute(self) -> _Result:
        rows = self.db.setdefault(self.name, [])
        if self._op in ("upsert", "insert"):
            assert self._payload is not None
            if self._op == "upsert":
                rows[:] = [r for r in rows if r.get("id") != self._payload.get("id")]
            rows.append(dict(self._payload))
            return _Result(data=[dict(self._payload)])
        data = rows
        for k, v in self._filters:
            data = [r for r in data if r.get(k) == v]
        if self._limit is not None:
            data = data[: self._limit]
        return _Result(data=[dict(r) for r in data])


class FakeClient:
    def __init__(self) -> None:
        self.db: dict[str, list[dict]] = {}

    def table(self, name: str) -> FakeTable:
        return FakeTable(self.db, name)


def test_supabase_repo_roundtrip_case_assertion_evidence_audit():
    client = FakeClient()
    repo = SupabaseCaseRepository(client)
    case = new_case(tenant_id="t1", subject="u1", title="T", summary="S")
    repo.save_case(case)
    loaded = repo.get_case(case.id)
    assert loaded is not None
    assert loaded.tenant_id == "t1"
    assertion = new_assertion(
        case_id=case.id, text="c", kind=AssertionKind.CLAIM, created_by="user", requires_evidence=True
    )
    repo.save_assertion(assertion)
    assert len(repo.list_assertions(case.id)) == 1
    evidence = new_evidence(
        case_id=case.id,
        assertion_id=assertion.id,
        body="body",
        source_type=EvidenceSourceType.USER_TEXT,
        source_uri=None,
        note=None,
        subject="u1",
    )
    repo.save_evidence(evidence)
    assert len(repo.list_evidence(case.id)) == 1
    repo.save_audit(
        AuditEvent(
            id="a1",
            tenant_id="t1",
            actor_subject="u1",
            action="case.created",
            object_type="case",
            object_id=case.id,
            payload_digest="abc",
            metadata={"k": 1},
            created_at=datetime.now(timezone.utc),
        )
    )
    assert len(repo.list_audit(case.id)) == 1


def test_store_defaults_to_memory(monkeypatch):
    reset_case_repository_cache()
    monkeypatch.delenv("INTEL_CASE_STORE", raising=False)
    repo = get_case_repository()
    assert isinstance(repo, InMemoryCaseRepository)
    reset_case_repository_cache()


def test_store_supabase_requires_env(monkeypatch):
    reset_case_repository_cache()
    monkeypatch.setenv("INTEL_CASE_STORE", "supabase")
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_SECRET_KEY", raising=False)
    with pytest.raises(CaseStoreConfigurationError):
        get_case_repository()
    reset_case_repository_cache()


def test_service_still_isolates_tenants_with_memory():
    repo = InMemoryCaseRepository()
    service = CaseService(repo)
    auth_a = AuthorizationContext(
        Identity("u", "tenant-a"),
        Permissions(frozenset({Capability.CASE_CREATE, Capability.CASE_READ})),
    )
    auth_b = AuthorizationContext(
        Identity("u", "tenant-b"),
        Permissions(frozenset({Capability.CASE_READ})),
    )
    case = service.create(auth_a, "hello")
    with pytest.raises(PolicyDeniedError):
        service.get(auth_b, case.id)
