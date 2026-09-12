"""Pure domain contracts for governed case intake.

This module deliberately has no HTTP, Supabase, or model-provider dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Optional
from uuid import uuid4


class CaseStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class AssertionKind(str, Enum):
    FACT = "fact"
    CLAIM = "claim"
    INFERENCE = "inference"
    UNKNOWN = "unknown"


class EvidenceSourceType(str, Enum):
    USER_TEXT = "user_text"
    URL = "url"
    DOCUMENT_REF = "document_ref"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _id() -> str:
    return str(uuid4())


@dataclass
class Case:
    id: str
    tenant_id: str
    created_by_subject: str
    title: str
    summary: str
    status: CaseStatus = CaseStatus.OPEN
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    missing_evidence_questions: list[str] = field(default_factory=list)


@dataclass
class Assertion:
    id: str
    case_id: str
    text: str
    kind: AssertionKind
    created_by: str
    requires_evidence: bool
    created_at: datetime = field(default_factory=_now)
    evidence_ids: list[str] = field(default_factory=list)


@dataclass
class Evidence:
    id: str
    case_id: str
    assertion_id: Optional[str]
    body: str
    source_type: EvidenceSourceType
    source_uri: Optional[str]
    note: Optional[str]
    created_by_subject: str
    created_at: datetime = field(default_factory=_now)


@dataclass(frozen=True)
class AuditEvent:
    id: str
    tenant_id: str
    actor_subject: str
    action: str
    object_type: str
    object_id: str
    payload_digest: str
    metadata: Mapping[str, Any]
    created_at: datetime = field(default_factory=_now)


@dataclass
class CaseAggregate:
    case: Case
    assertions: list[Assertion]
    evidence: list[Evidence]
    audit_events: list[AuditEvent]
    missing_evidence_questions: list[str] = field(default_factory=list)


def new_case(*, tenant_id: str, subject: str, title: str, summary: str) -> Case:
    return Case(id=_id(), tenant_id=tenant_id, created_by_subject=subject, title=title, summary=summary)


def new_assertion(*, case_id: str, text: str, kind: AssertionKind, created_by: str, requires_evidence: bool) -> Assertion:
    return Assertion(id=_id(), case_id=case_id, text=text, kind=kind, created_by=created_by, requires_evidence=requires_evidence)


def new_evidence(*, case_id: str, assertion_id: Optional[str], body: str, source_type: EvidenceSourceType,
                 source_uri: Optional[str], note: Optional[str], subject: str) -> Evidence:
    return Evidence(id=_id(), case_id=case_id, assertion_id=assertion_id, body=body, source_type=source_type,
                    source_uri=source_uri, note=note, created_by_subject=subject)
