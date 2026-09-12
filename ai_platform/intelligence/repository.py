"""Repository contracts and a deterministic in-memory implementation.

The interface keeps persistence replaceable. The v1 API uses this implementation;
production persistence can be added behind the same contract without changing the domain.
"""
from __future__ import annotations

from copy import deepcopy
from threading import RLock
from typing import Protocol

from .models import Assertion, AuditEvent, Case, Evidence


class CaseRepository(Protocol):
    def save_case(self, case: Case) -> None: ...
    def get_case(self, case_id: str) -> Case | None: ...
    def save_assertion(self, assertion: Assertion) -> None: ...
    def list_assertions(self, case_id: str) -> list[Assertion]: ...
    def save_evidence(self, evidence: Evidence) -> None: ...
    def list_evidence(self, case_id: str) -> list[Evidence]: ...
    def save_audit(self, event: AuditEvent) -> None: ...
    def list_audit(self, object_id: str) -> list[AuditEvent]: ...


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

    def list_audit(self, object_id: str) -> list[AuditEvent]:
        with self._lock:
            return [deepcopy(x) for x in self._audits.values() if x.object_id == object_id]
