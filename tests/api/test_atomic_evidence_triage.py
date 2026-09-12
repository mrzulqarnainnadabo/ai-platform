"""Failure-injection and tenant-invariant coverage for atomic intelligence writes."""

from datetime import datetime, timezone

import pytest

from ai_platform.intelligence.models import AssertionKind, AuditEvent, EvidenceSourceType, new_assertion, new_case, new_evidence
from ai_platform.intelligence.repository import InMemoryCaseRepository
from ai_platform.intelligence.supabase_repository import SupabaseCaseRepository


def audit(case_id: str, tenant_id: str, action: str, audit_id: str) -> AuditEvent:
    return AuditEvent(id=audit_id, tenant_id=tenant_id, actor_subject="user-1", action=action,
                      object_type="case", object_id=case_id, payload_digest="digest", metadata={},
                      created_at=datetime.now(timezone.utc))


class _FailingDict(dict):
    def __setitem__(self, key, value):
        raise RuntimeError("injected persistence failure")


def seeded_repository():
    repository = InMemoryCaseRepository()
    case = new_case(tenant_id="tenant-1", subject="user-1", title="case", summary="summary")
    assertion = new_assertion(case_id=case.id, text="claim", kind=AssertionKind.CLAIM,
                              created_by="user", requires_evidence=True)
    repository.create_case_bundle(case, assertion, audit(case.id, case.tenant_id, "case.created", "audit-create"))
    return repository, case, assertion


def test_evidence_bundle_rolls_back_when_audit_write_fails():
    repository, case, assertion = seeded_repository()
    before_assertion = repository.list_assertions(case.id)[0]
    repository._audits = _FailingDict(repository._audits)
    evidence = new_evidence(case_id=case.id, assertion_id=assertion.id, body="source",
                            source_type=EvidenceSourceType.USER_TEXT, source_uri=None, note=None, subject="user-1")
    updated_assertion = new_assertion(case_id=case.id, text=assertion.text, kind=assertion.kind,
                                      created_by=assertion.created_by, requires_evidence=assertion.requires_evidence)
    updated_assertion.id = assertion.id
    updated_assertion.evidence_ids = [evidence.id]

    with pytest.raises(RuntimeError, match="injected persistence failure"):
        repository.attach_evidence_bundle(evidence, updated_assertion,
                                          audit(case.id, case.tenant_id, "evidence.attached", "audit-evidence"))

    assert repository.list_evidence(case.id) == []
    assert repository.list_assertions(case.id)[0] == before_assertion
    assert [x.action for x in repository.list_audit(case.id)] == ["case.created"]


def test_triage_bundle_rolls_back_when_audit_write_fails():
    repository, case, _ = seeded_repository()
    case.status = "in_progress"  # enum-compatible value is not required by repository storage
    assertion = new_assertion(case_id=case.id, text="generated claim", kind=AssertionKind.CLAIM,
                              created_by="model", requires_evidence=True)
    before_case = repository.get_case(case.id)
    before_assertions = repository.list_assertions(case.id)
    repository._audits = _FailingDict(repository._audits)

    with pytest.raises(RuntimeError, match="injected persistence failure"):
        repository.save_triage_bundle(case, [assertion], audit(case.id, case.tenant_id, "case.triaged", "audit-triage"))

    assert repository.get_case(case.id) == before_case
    assert repository.list_assertions(case.id) == before_assertions
    assert [x.action for x in repository.list_audit(case.id)] == ["case.created"]


def test_evidence_bundle_rejects_cross_tenant_audit_before_write():
    repository, case, assertion = seeded_repository()
    evidence = new_evidence(case_id=case.id, assertion_id=assertion.id, body="source",
                            source_type=EvidenceSourceType.USER_TEXT, source_uri=None, note=None, subject="user-1")
    assertion.evidence_ids = [evidence.id]
    with pytest.raises(ValueError, match="tenant"):
        repository.attach_evidence_bundle(evidence, assertion,
                                          audit(case.id, "tenant-2", "evidence.attached", "audit-cross-tenant"))
    assert repository.list_evidence(case.id) == []
    assert repository.list_assertions(case.id)[0].evidence_ids == []


def test_triage_bundle_rejects_cross_tenant_audit_before_write():
    repository, case, _ = seeded_repository()
    assertion = new_assertion(case_id=case.id, text="generated", kind=AssertionKind.CLAIM,
                              created_by="model", requires_evidence=True)
    with pytest.raises(ValueError, match="tenant"):
        repository.save_triage_bundle(case, [assertion], audit(case.id, "tenant-2", "case.triaged", "audit-cross-tenant"))
    assert repository.list_assertions(case.id) == [repository.list_assertions(case.id)[0]]


class _RpcResponse:
    def execute(self):
        return self


class _RpcClient:
    def __init__(self):
        self.calls = []

    def rpc(self, name, params):
        self.calls.append((name, params))
        return _RpcResponse()


def test_supabase_evidence_and_triage_use_transactional_rpcs():
    client = _RpcClient()
    repository = SupabaseCaseRepository(client)
    case = new_case(tenant_id="tenant-1", subject="user-1", title="case", summary="summary")
    assertion = new_assertion(case_id=case.id, text="claim", kind=AssertionKind.CLAIM,
                              created_by="user", requires_evidence=True)
    evidence = new_evidence(case_id=case.id, assertion_id=assertion.id, body="source",
                            source_type=EvidenceSourceType.USER_TEXT, source_uri=None, note=None, subject="user-1")
    assertion.evidence_ids.append(evidence.id)
    repository.attach_evidence_bundle(evidence, assertion, audit(case.id, case.tenant_id, "evidence.attached", "audit-1"))
    repository.save_triage_bundle(case, [assertion], audit(case.id, case.tenant_id, "case.triaged", "audit-2"))

    assert [name for name, _ in client.calls] == ["attach_evidence_bundle", "save_triage_bundle"]
    assert client.calls[0][1]["p_assertion_id"] == assertion.id
    assert client.calls[1][1]["p_case"]["tenant_id"] == case.tenant_id
    assert client.calls[1][1]["p_assertions"][0]["case_id"] == case.id
