import asyncio
from types import SimpleNamespace

import pytest

from ai_platform.core.messages import Message
from ai_platform.intelligence.models import AssertionKind, EvidenceSourceType
from ai_platform.intelligence.repository import InMemoryCaseRepository
from ai_platform.intelligence.service import CaseService, EvidenceService
from ai_platform.intelligence.triage import parse_triage_output
from ai_platform.policy.authorization import AuthorizationContext, Identity, Permissions
from ai_platform.policy.capabilities import Capability
from ai_platform.policy.errors import PolicyDeniedError


def auth(*caps: Capability, tenant: str = "tenant-a") -> AuthorizationContext:
    return AuthorizationContext(Identity("user-1", tenant), Permissions(frozenset(caps)))


def test_assertion_kind_validation_discards_invalid_and_fact_without_evidence():
    parsed = parse_triage_output(
        '{"assertions":['
        '{"text":"A","kind":"claim"},'
        '{"text":"B","kind":"fact"},'
        '{"text":"C","kind":"made_up"}'
        '],"missing_evidence_questions":["Where is the record?"]}'
    )
    assert [(x["text"], x["kind"]) for x in parsed.assertions] == [("A", AssertionKind.CLAIM)]
    assert parsed.missing_evidence_questions == ["Where is the record?"]


def test_create_requires_capability_and_emits_audit():
    repo = InMemoryCaseRepository()
    service = CaseService(repo)
    with pytest.raises(PolicyDeniedError):
        service.create(auth(), "No permission")

    case = service.create(auth(Capability.CASE_CREATE), "Clinic has no medicines")
    aggregate = CaseService(repo).get(auth(Capability.CASE_READ), case.id)
    assert aggregate.case.tenant_id == "tenant-a"
    assert aggregate.assertions[0].kind == AssertionKind.UNKNOWN
    assert [event.action for event in aggregate.audit_events] == ["case.created"]


def test_create_aggregate_does_not_require_read_capability():
    repo = InMemoryCaseRepository()
    service = CaseService(repo)
    aggregate = service.create_aggregate(auth(Capability.CASE_CREATE), "Create-only case")
    assert aggregate.case.summary == "Create-only case"
    assert aggregate.assertions[0].kind == AssertionKind.UNKNOWN
    assert aggregate.audit_events[0].action == "case.created"


def test_cross_tenant_read_is_denied():
    repo = InMemoryCaseRepository()
    service = CaseService(repo)
    case = service.create(auth(Capability.CASE_CREATE), "Private case")
    with pytest.raises(PolicyDeniedError):
        service.get(auth(Capability.CASE_READ, tenant="tenant-b"), case.id)


def test_cross_tenant_evidence_is_denied():
    repo = InMemoryCaseRepository()
    case_service = CaseService(repo)
    evidence_service = EvidenceService(repo)
    case = case_service.create(auth(Capability.CASE_CREATE), "Tenant A case")
    with pytest.raises(PolicyDeniedError):
        evidence_service.attach(
            auth(Capability.EVIDENCE_ATTACH, tenant="tenant-b"),
            case.id,
            body="forged",
            source_type=EvidenceSourceType.USER_TEXT,
            source_uri=None,
            note=None,
            assertion_id=None,
        )


def test_cross_case_assertion_link_is_denied():
    repo = InMemoryCaseRepository()
    case_service = CaseService(repo)
    evidence_service = EvidenceService(repo)
    case_a = case_service.create(auth(Capability.CASE_CREATE), "Case A")
    case_b = case_service.create(auth(Capability.CASE_CREATE), "Case B")
    assertion_b = case_service.get(auth(Capability.CASE_READ), case_b.id).assertions[0]
    with pytest.raises(ValueError):
        evidence_service.attach(
            auth(Capability.EVIDENCE_ATTACH),
            case_a.id,
            body="link attempt",
            source_type=EvidenceSourceType.USER_TEXT,
            source_uri=None,
            note=None,
            assertion_id=assertion_b.id,
        )


def test_triage_requires_capability_before_model_call():
    repo = InMemoryCaseRepository()
    service = CaseService(repo)
    case = service.create(auth(Capability.CASE_CREATE), "Problem report")

    class NeverCalled:
        async def generate(self, *args, **kwargs):
            raise AssertionError("model must not be called")

    with pytest.raises(PolicyDeniedError):
        asyncio.run(service.triage(auth(Capability.CASE_READ), case.id, NeverCalled(), model_name="test"))


def test_triage_requires_model_generate_before_model_call():
    repo = InMemoryCaseRepository()
    service = CaseService(repo)
    case = service.create(auth(Capability.CASE_CREATE), "Problem report")

    class NeverCalled:
        async def generate(self, *args, **kwargs):
            raise AssertionError("model must not be called")

    with pytest.raises(PolicyDeniedError):
        asyncio.run(
            service.triage(
                auth(Capability.CASE_TRIAGE),
                case.id,
                NeverCalled(),
                model_name="test",
            )
        )


def test_triage_persists_model_assertions_and_questions():
    repo = InMemoryCaseRepository()
    service = CaseService(repo)
    case = service.create(auth(Capability.CASE_CREATE), "Clinic has no medicines")

    class FakeRuntime:
        async def generate(self, *args, **kwargs):
            response = SimpleNamespace(message=Message(role="assistant", content=(
                '{"assertions":[{"text":"Medicines are unavailable","kind":"claim"},'
                '{"text":"This may affect patients","kind":"inference"},'
                '{"text":"Unsupported fact","kind":"fact"}],'
                '"missing_evidence_questions":["Can staff provide stock records?"]}'
            )))
            return SimpleNamespace(response=response)

    aggregate = asyncio.run(service.triage(
        auth(
            Capability.CASE_CREATE,
            Capability.CASE_READ,
            Capability.CASE_TRIAGE,
            Capability.MODEL_GENERATE,
        ),
        case.id,
        FakeRuntime(),
        model_name="test",
    ))
    model_assertions = [x for x in aggregate.assertions if x.created_by == "model"]
    assert [x.kind for x in model_assertions] == [AssertionKind.CLAIM, AssertionKind.INFERENCE]
    assert aggregate.missing_evidence_questions == ["Can staff provide stock records?"]
    assert [event.action for event in aggregate.audit_events] == ["case.created", "case.triaged"]


def test_evidence_requires_provenance_and_emits_case_scoped_audit():
    repo = InMemoryCaseRepository()
    case_service = CaseService(repo)
    evidence_service = EvidenceService(repo)
    case = case_service.create(auth(Capability.CASE_CREATE), "Evidence test")
    with pytest.raises(ValueError):
        evidence_service.attach(
            auth(Capability.EVIDENCE_ATTACH), case.id, body="source", source_type=EvidenceSourceType.URL,
            source_uri=None, note=None, assertion_id=None,
        )
    with pytest.raises(ValueError):
        evidence_service.attach(
            auth(Capability.EVIDENCE_ATTACH), case.id, body="source", source_type=EvidenceSourceType.URL,
            source_uri="   ", note=None, assertion_id=None,
        )
    evidence = evidence_service.attach(
        auth(Capability.EVIDENCE_ATTACH), case.id, body="record excerpt", source_type=EvidenceSourceType.DOCUMENT_REF,
        source_uri=" document:stock-record-1 ", note="provided by reporter", assertion_id=None,
    )
    assert evidence.source_uri == "document:stock-record-1"
    aggregate = case_service.get(auth(Capability.CASE_READ), case.id)
    assert [event.action for event in aggregate.audit_events] == ["case.created", "evidence.attached"]
    attached = next(e for e in aggregate.audit_events if e.action == "evidence.attached")
    assert attached.metadata.get("evidence_id") == evidence.id
    assert "record excerpt" not in str(attached.metadata)
