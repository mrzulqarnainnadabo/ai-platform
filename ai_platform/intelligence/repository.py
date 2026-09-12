"""Case repository contracts.

In-memory implementation is a deliberate vertical-slice boundary;
production persistence can be added behind the same contract without changing the domain.

InMemoryCaseRepository is NOT production durable storage: data is process-local and lost on restart.
"""
from __future__ import annotations

from copy import deepcopy
from threading import RLock
from typing import Protocol

from .models import Assertion, AuditEvent, Case, Evidence


class CaseRepository(Protocol):
    def save_case(self, case: Case) -> None: ...
    def get_case(self, case_id: str) -> Case | None: ...
    def list_cases(self, tenant_id: str) -> list[Case]: ...
    def save_assertion(self, assertion: Assertion) -> None: ...
    def list_assertions(self, case_id: str) -> list[Assertion]: ...
    def save_evidence(self, evidence: Evidence) -> None: ...
    def list_evidence(self, case_id: str) -> list[Evidence]: ...
    def save_audit(self, event: AuditEvent) -> None: ...
    def list_audit(self, object_id: str, tenant_id: str | None = None) -> list[AuditEvent]: ...
    def create_case_bundle(self, case: Case, assertion: Assertion, audit: AuditEvent) -> None: ...
    def attach_evidence_bundle(self, evidence: Evidence, assertion: Assertion | None, audit: AuditEvent) -> None: ...
    def save_triage_bundle(self, case: Case, assertions: list[Assertion], audit: AuditEvent) -> None: ...


class InMemoryCaseRepository:
    def __init__(self) -> None:
        self._cases: dict[str, Case] = {}
        self._assertions: dict[str, Assertion] = {}
        self._evidence: dict[str, Evidence] = {}
        self._audits: dict[str, AuditEvent] = {}
        self._lock = RLock()

    def save_case(self, case: Case) -> None:
        with self._lock:
            self._cases[case.id] = deepcopy(case)

    def get_case(self, case_id: str) -> Case | None:
        with self._lock:
            case = self._cases.get(case_id)
            return deepcopy(case) if case else None

    def list_cases(self, tenant_id: str) -> list[Case]:
        with self._lock:
            return [deepcopy(x) for x in self._cases.values() if x.tenant_id == tenant_id]

    def save_assertion(self, assertion: Assertion) -> None:
        with self._lock:
            self._assertions[assertion.id] = deepcopy(assertion)

    def list_assertions(self, case_id: str) -> list[Assertion]:
        with self._lock:
            return [deepcopy(x) for x in self._assertions.values() if x.case_id == case_id]

    def save_evidence(self, evidence: Evidence) -> None:
        with self._lock:
            self._evidence[evidence.id] = deepcopy(evidence)

    def list_evidence(self, case_id: str) -> list[Evidence]:
        with self._lock:
            return [deepcopy(x) for x in self._evidence.values() if x.case_id == case_id]

    def save_audit(self, event: AuditEvent) -> None:
        with self._lock:
            self._audits[event.id] = deepcopy(event)

    def list_audit(self, object_id: str, tenant_id: str | None = None) -> list[AuditEvent]:
        with self._lock:
            return [deepcopy(x) for x in self._audits.values() if x.object_id == object_id and (tenant_id is None or x.tenant_id == tenant_id)]

    def _snapshot(self) -> tuple[dict[str, Case], dict[str, Assertion], dict[str, Evidence], dict[str, AuditEvent]]:
        return deepcopy((self._cases, self._assertions, self._evidence, self._audits))

    def _restore(self, snapshot: tuple[dict[str, Case], dict[str, Assertion], dict[str, Evidence], dict[str, AuditEvent]]) -> None:
        self._cases, self._assertions, self._evidence, self._audits = snapshot

    def create_case_bundle(self, case: Case, assertion: Assertion, audit: AuditEvent) -> None:
        with self._lock:
            if assertion.case_id != case.id or audit.object_id != case.id:
                raise ValueError("case bundle references do not match case")
            if assertion.id in self._assertions or case.id in self._cases or audit.id in self._audits:
                raise ValueError("case bundle contains an existing identifier")
            if audit.tenant_id != case.tenant_id:
                raise ValueError("case bundle tenant references do not match case")
            snapshot = self._snapshot()
            try:
                self._cases[case.id] = deepcopy(case)
                self._assertions[assertion.id] = deepcopy(assertion)
                self._audits[audit.id] = deepcopy(audit)
            except Exception:
                self._restore(snapshot)
                raise

    def attach_evidence_bundle(self, evidence: Evidence, assertion: Assertion | None, audit: AuditEvent) -> None:
        with self._lock:
            case = self._cases.get(evidence.case_id)
            if case is None:
                raise ValueError("evidence case does not exist")
            if evidence.assertion_id and assertion is None:
                raise ValueError("linked evidence requires assertion")
            if assertion is not None:
                if assertion.id != evidence.assertion_id or assertion.case_id != evidence.case_id:
                    raise ValueError("evidence assertion reference does not match case")
                if assertion.id not in self._assertions:
                    raise ValueError("assertion does not exist")
            if evidence.id in self._evidence or audit.id in self._audits:
                raise ValueError("evidence bundle contains an existing identifier")
            if audit.object_id != evidence.case_id or audit.tenant_id != case.tenant_id:
                raise ValueError("evidence bundle tenant references do not match case")
            snapshot = self._snapshot()
            try:
                self._evidence[evidence.id] = deepcopy(evidence)
                if assertion is not None:
                    self._assertions[assertion.id] = deepcopy(assertion)
                self._audits[audit.id] = deepcopy(audit)
            except Exception:
                self._restore(snapshot)
                raise

    def save_triage_bundle(self, case: Case, assertions: list[Assertion], audit: AuditEvent) -> None:
        with self._lock:
            stored_case = self._cases.get(case.id)
            if stored_case is None:
                raise ValueError("triage case does not exist")
            if case.tenant_id != stored_case.tenant_id or audit.tenant_id != case.tenant_id or audit.object_id != case.id:
                raise ValueError("triage bundle tenant references do not match case")
            ids = [x.id for x in assertions]
            if len(ids) != len(set(ids)) or any(x.case_id != case.id for x in assertions):
                raise ValueError("triage assertion references do not match case")
            if any(x.id in self._assertions for x in assertions) or audit.id in self._audits:
                raise ValueError("triage bundle contains an existing identifier")
            snapshot = self._snapshot()
            try:
                self._assertions.update({x.id: deepcopy(x) for x in assertions})
                self._cases[case.id] = deepcopy(case)
                self._audits[audit.id] = deepcopy(audit)
            except Exception:
                self._restore(snapshot)
                raise
