"""Regression coverage for atomic case aggregate creation."""

from datetime import datetime, timezone

import pytest

from ai_platform.intelligence.models import AssertionKind, AuditEvent, new_assertion, new_case
from ai_platform.intelligence.repository import InMemoryCaseRepository
from ai_platform.intelligence.service import CaseService
from ai_platform.policy.authorization import AuthorizationContext, Identity, Permissions
from ai_platform.policy.capabilities import Capability
from ai_platform.intelligence.supabase_repository import SupabaseCaseRepository


def auth_context(tenant_id: str = "tenant-1") -> AuthorizationContext:
    return AuthorizationContext(
        identity=Identity(subject="user-1", tenant_id=tenant_id),
        permissions=Permissions(frozenset({Capability.CASE_CREATE})),
    )


def test_case_creation_uses_one_atomic_repository_operation():
    repository = InMemoryCaseRepository()
    service = CaseService(repository)

    case = service.create(auth_context(), "atomic case")

    assert repository.get_case(case.id) is not None
    assertions = repository.list_assertions(case.id)
    assert len(assertions) == 1
    assert assertions[0].kind == AssertionKind.UNKNOWN
    audits = repository.list_audit(case.id)
    assert len(audits) == 1
    assert audits[0].action == "case.created"


def test_case_bundle_validation_happens_before_any_in_memory_write():
    repository = InMemoryCaseRepository()
    case = new_case(tenant_id="tenant-1", subject="user-1", title="case", summary="summary")
    assertion = new_assertion(case_id=case.id, text="summary", kind=AssertionKind.UNKNOWN,
                              created_by="user", requires_evidence=True)
    audit = AuditEvent(
        id="audit-1",
        tenant_id="tenant-2",
        actor_subject="user-1",
        action="case.created",
        object_type="case",
        object_id=case.id,
        payload_digest="digest",
        metadata={},
        created_at=datetime.now(timezone.utc),
    )

    with pytest.raises(ValueError, match="tenant references"):
        repository.create_case_bundle(case, assertion, audit)

    assert repository._cases == {}
    assert repository._assertions == {}
    assert repository._audits == {}


class _RpcResponse:
    def execute(self):
        return self


class _RpcClient:
    def __init__(self):
        self.calls = []

    def rpc(self, name, params):
        self.calls.append((name, params))
        return _RpcResponse()


def test_supabase_repository_uses_transactional_rpc():
    client = _RpcClient()
    repository = SupabaseCaseRepository(client)
    case = new_case(tenant_id="tenant-1", subject="user-1", title="case", summary="summary")
    assertion = new_assertion(case_id=case.id, text="summary", kind=AssertionKind.UNKNOWN,
                              created_by="user", requires_evidence=True)
    audit = AuditEvent(
        id="audit-1",
        tenant_id="tenant-1",
        actor_subject="user-1",
        action="case.created",
        object_type="case",
        object_id=case.id,
        payload_digest="digest",
        metadata={"keys": ["status", "initial_assertion"]},
        created_at=datetime.now(timezone.utc),
    )

    repository.create_case_bundle(case, assertion, audit)

    assert len(client.calls) == 1
    name, params = client.calls[0]
    assert name == "create_case_bundle"
    assert params["p_case"]["id"] == case.id
    assert params["p_assertion"]["case_id"] == case.id
    assert params["p_audit"]["object_id"] == case.id
