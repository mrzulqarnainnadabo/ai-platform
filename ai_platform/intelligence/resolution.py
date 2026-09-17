"""Governed civic problem-resolution domain.

The resolution layer deliberately separates AI-generated proposals from
human-authorized commitments. AI may suggest an action; it cannot create a
commitment or mark an outcome without an explicit authorized transition.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4


class ActionProposalStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class CommitmentStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OutcomeStatus(str, Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    ACHIEVED = "achieved"
    NOT_ACHIEVED = "not_achieved"
    VERIFIED = "verified"


@dataclass
class Responsibility:
    id: str
    case_id: str
    tenant_id: str
    subject: str
    role: str
    scope: str
    source_assertion_ids: list[str] = field(default_factory=list)
    status: str = "proposed"
    created_by_subject: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ActionProposal:
    id: str
    case_id: str
    tenant_id: str
    title: str
    description: str
    proposed_by_subject: str
    responsibility_id: Optional[str] = None
    source_assertion_ids: list[str] = field(default_factory=list)
    status: ActionProposalStatus = ActionProposalStatus.DRAFT
    approval_subject: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Commitment:
    id: str
    case_id: str
    tenant_id: str
    proposal_id: str
    owner_subject: str
    action: str
    due_at: Optional[datetime] = None
    status: CommitmentStatus = CommitmentStatus.PENDING
    created_by_subject: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Outcome:
    id: str
    case_id: str
    tenant_id: str
    commitment_id: str
    summary: str
    status: OutcomeStatus
    evidence_ids: list[str] = field(default_factory=list)
    recorded_by_subject: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def new_responsibility(*, case_id: str, tenant_id: str, subject: str, role: str, scope: str,
                       created_by_subject: str, source_assertion_ids: Optional[list[str]] = None) -> Responsibility:
    return Responsibility(id=uuid4().hex, case_id=case_id, tenant_id=tenant_id, subject=subject,
                          role=role, scope=scope, created_by_subject=created_by_subject,
                          source_assertion_ids=list(source_assertion_ids or []))


def new_action_proposal(*, case_id: str, tenant_id: str, title: str, description: str,
                        proposed_by_subject: str, responsibility_id: Optional[str] = None,
                        source_assertion_ids: Optional[list[str]] = None) -> ActionProposal:
    return ActionProposal(id=uuid4().hex, case_id=case_id, tenant_id=tenant_id, title=title,
                          description=description, proposed_by_subject=proposed_by_subject,
                          responsibility_id=responsibility_id,
                          source_assertion_ids=list(source_assertion_ids or []))


def new_commitment(*, case_id: str, tenant_id: str, proposal_id: str, owner_subject: str,
                   action: str, created_by_subject: str, due_at: Optional[datetime] = None) -> Commitment:
    return Commitment(id=uuid4().hex, case_id=case_id, tenant_id=tenant_id, proposal_id=proposal_id,
                      owner_subject=owner_subject, action=action, created_by_subject=created_by_subject,
                      due_at=due_at)


def new_outcome(*, case_id: str, tenant_id: str, commitment_id: str, summary: str,
                status: OutcomeStatus, recorded_by_subject: str,
                evidence_ids: Optional[list[str]] = None) -> Outcome:
    return Outcome(id=uuid4().hex, case_id=case_id, tenant_id=tenant_id, commitment_id=commitment_id,
                   summary=summary, status=status, recorded_by_subject=recorded_by_subject,
                   evidence_ids=list(evidence_ids or []))
