"""Focused regression coverage for governed intelligence case intake."""

import asyncio

import pytest

from api.cases_frontend import cases_page
from ai_platform.intelligence.models import EvidenceSourceType
from ai_platform.intelligence.repository import InMemoryCaseRepository
from ai_platform.intelligence.service import CaseNotFoundError, CaseService, EvidenceService, InvalidCaseInput
from ai_platform.intelligence.store import CaseStoreConfigurationError, get_case_repository, reset_case_repository_cache
from ai_platform.policy.authorization import AuthorizationContext, Identity, Permissions
from ai_platform.policy.capabilities import Capability
from ai_platform.policy.errors import PolicyDeniedError
from ai_platform.runtime.authorized import AuthorizedModelRuntime
from ai_platform.runtime.model_runtime import ModelRuntime
from ai_platform.runtime.registry import ProviderRegistry


def auth_context(*capabilities: Capability, tenant_id: str = "tenant-1") -> AuthorizationContext:
    return AuthorizationContext(
        identity=Identity(subject="user-1", tenant_id=tenant_id),
        permissions=Permissions(frozenset(capabilities)),
    )


def test_supabase_store_fails_closed_when_server_credentials_are_missing(monkeypatch):
    monkeypatch.setenv("INTEL_CASE_STORE", "supabase")
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_SECRET_KEY", raising=False)
    reset_case_repository_cache()
    try:
        with pytest.raises(CaseStoreConfigurationError, match="SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY"):
            get_case_repository()
    finally:
        reset_case_repository_cache()


def test_case_creation_is_denied_before_repository_write():
    repository = InMemoryCaseRepository()
    service = CaseService(repository)

    with pytest.raises(PolicyDeniedError):
        service.create(auth_context(), "should not be stored")

    assert repository._cases == {}
    assert repository._assertions == {}
    assert repository._audits == {}


def test_get_case_returns_not_found_for_unknown_case_id():
    service = CaseService(InMemoryCaseRepository())

    with pytest.raises(CaseNotFoundError):
        service.get(auth_context(Capability.CASE_READ), "does-not-exist")


def test_evidence_requires_an_assertion_from_the_same_case():
    repository = InMemoryCaseRepository()
    service = CaseService(repository)
    evidence_service = EvidenceService(repository)
    auth = auth_context(Capability.CASE_CREATE, Capability.EVIDENCE_ATTACH)

    first_case = service.create(auth, "first case")
    second_case = service.create(auth, "second case")
    second_assertion = repository.list_assertions(second_case.id)[0]

    with pytest.raises(InvalidCaseInput, match="does not belong to this case"):
        evidence_service.attach(
            auth,
            first_case.id,
            body="evidence",
            source_type=EvidenceSourceType.USER_TEXT,
            source_uri=None,
            note=None,
            assertion_id=second_assertion.id,
        )

    assert repository.list_evidence(first_case.id) == []


def test_triage_fails_before_model_execution_for_unknown_provider():
    repository = InMemoryCaseRepository()
    service = CaseService(repository)
    auth = auth_context(Capability.CASE_CREATE, Capability.CASE_TRIAGE, Capability.MODEL_GENERATE)
    case = service.create(auth, "triage this case")
    runtime = AuthorizedModelRuntime(ModelRuntime(ProviderRegistry()))

    with pytest.raises(ValueError, match="Unknown provider"):
        asyncio.run(service.triage(auth, case.id, runtime, model_name="demo", provider_name="provider-that-is-not-registered"))

    stored = repository.get_case(case.id)
    assert stored is not None
    assert stored.status.value == "open"
    assert repository.list_evidence(case.id) == []


def test_case_listing_is_tenant_scoped():
    repository = InMemoryCaseRepository()
    service = CaseService(repository)
    create = auth_context(Capability.CASE_CREATE, tenant_id="tenant-a")
    other_create = auth_context(Capability.CASE_CREATE, tenant_id="tenant-b")
    read_a = auth_context(Capability.CASE_READ, tenant_id="tenant-a")

    first = service.create(create, "tenant a case")
    service.create(other_create, "tenant b case")

    listed = service.list(read_a)
    assert [case.id for case in listed] == [first.id]
    assert all(case.tenant_id == "tenant-a" for case in listed)


def test_cases_page_escapes_browser_configuration(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", 'https://example.supabase.co/"><script>alert(1)</script>')
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", 'public-key"><script>alert(2)</script>')

    body = cases_page().body.decode("utf-8")

    assert '<script>alert(1)</script>' not in body
    assert '<script>alert(2)</script>' not in body
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' not in body
    assert '\\u003cscript>alert(1)\\u003c/script>' in body
    assert '\\u003cscript>alert(2)\\u003c/script>' in body
