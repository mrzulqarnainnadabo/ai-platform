"""Deterministic service rules for civic problem resolution.

No model call is made here. AI-generated content must enter as a proposal and
still pass explicit authorization before it can become a commitment.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from ai_platform.policy.authorization import AuthorizationContext
from ai_platform.policy.capabilities import Capability
from ai_platform.policy.decisions import Decision
from ai_platform.policy.evaluator import SimplePermissionEvaluator
from ai_platform.policy.errors import PolicyDeniedError

from .resolution import (
    ActionProposal,
    ActionProposalStatus,
    Commitment,
    CommitmentStatus,
    Outcome,
    OutcomeStatus,
    Responsibility,
    new_action_proposal,
    new_commitment,
    new_outcome,
    new_responsibility,
)
from .resolution_repository import ResolutionRepository


class ResolutionNotFoundError(LookupError):
    pass


class InvalidResolutionTransition(ValueError):
    pass


class ResolutionService:
    """Fail-closed, tenant-scoped service for the resolution lifecycle."""

    def __init__(self, repository: ResolutionRepository, *, evaluator: Optional[SimplePermissionEvaluator] = None) -> None:
        self.repository = repository
        self.evaluator = evaluator or SimplePermissionEvaluator()

    def _authorize(self, auth: AuthorizationContext, capability: Capability) -> None:
        decision = self.evaluator.evaluate(auth, capability)
        if decision.decision != Decision.ALLOW:
            raise PolicyDeniedError(decision.reason)

    @staticmethod
    def _tenant(auth: AuthorizationContext, tenant_id: str) -> None:
        if auth.identity.tenant_id != tenant_id:
            raise PolicyDeniedError("Resolution tenant does not match authorization tenant")

    def propose_responsibility(self, auth: AuthorizationContext, *, case_id: str, subject: str,
                               role: str, scope: str, source_assertion_ids: Optional[list[str]] = None) -> Responsibility:
        self._authorize(auth, Capability.RESPONSIBILITY_PROPOSE)
        item = new_responsibility(case_id=case_id, tenant_id=auth.identity.tenant_id, subject=subject,
                                  role=role, scope=scope, created_by_subject=auth.identity.subject,
                                  source_assertion_ids=source_assertion_ids)
        self.repository.save_responsibility(item)
        return item

    def propose_action(self, auth: AuthorizationContext, *, case_id: str, title: str, description: str,
                       responsibility_id: Optional[str] = None, source_assertion_ids: Optional[list[str]] = None) -> ActionProposal:
        self._authorize(auth, Capability.ACTION_PROPOSE)
        if not title.strip() or not description.strip():
            raise InvalidResolutionTransition("Action proposal title and description are required")
        if responsibility_id:
            responsibility = self.repository.get_responsibility(responsibility_id)
            if responsibility is None:
                raise ResolutionNotFoundError(responsibility_id)
            self._tenant(auth, responsibility.tenant_id)
            if responsibility.case_id != case_id:
                raise InvalidResolutionTransition("Responsibility does not belong to case")
        item = new_action_proposal(case_id=case_id, tenant_id=auth.identity.tenant_id, title=title.strip(),
                                   description=description.strip(), proposed_by_subject=auth.identity.subject,
                                   responsibility_id=responsibility_id, source_assertion_ids=source_assertion_ids)
        self.repository.save_proposal(item)
        return item

    def approve_action(self, auth: AuthorizationContext, proposal_id: str) -> ActionProposal:
        self._authorize(auth, Capability.ACTION_APPROVE)
        item = self.repository.get_proposal(proposal_id)
        if item is None:
            raise ResolutionNotFoundError(proposal_id)
        self._tenant(auth, item.tenant_id)
        if item.status != ActionProposalStatus.SUBMITTED:
            raise InvalidResolutionTransition("Only submitted proposals can be approved")
        item.status = ActionProposalStatus.APPROVED
        item.approval_subject = auth.identity.subject
        item.approved_at = datetime.now(item.created_at.tzinfo)
        self.repository.save_proposal(item)
        return item

    def submit_action(self, auth: AuthorizationContext, proposal_id: str) -> ActionProposal:
        self._authorize(auth, Capability.ACTION_PROPOSE)
        item = self.repository.get_proposal(proposal_id)
        if item is None:
            raise ResolutionNotFoundError(proposal_id)
        self._tenant(auth, item.tenant_id)
        if item.status != ActionProposalStatus.DRAFT:
            raise InvalidResolutionTransition("Only draft proposals can be submitted")
        item.status = ActionProposalStatus.SUBMITTED
        self.repository.save_proposal(item)
        return item

    def create_commitment(self, auth: AuthorizationContext, *, proposal_id: str, owner_subject: str,
                          action: str, due_at: Optional[datetime] = None) -> Commitment:
        self._authorize(auth, Capability.COMMITMENT_CREATE)
        proposal = self.repository.get_proposal(proposal_id)
        if proposal is None:
            raise ResolutionNotFoundError(proposal_id)
        self._tenant(auth, proposal.tenant_id)
        if proposal.status != ActionProposalStatus.APPROVED:
            raise InvalidResolutionTransition("A commitment requires an approved action proposal")
        if not owner_subject.strip() or not action.strip():
            raise InvalidResolutionTransition("Commitment owner and action are required")
        item = new_commitment(case_id=proposal.case_id, tenant_id=proposal.tenant_id, proposal_id=proposal.id,
                              owner_subject=owner_subject.strip(), action=action.strip(),
                              created_by_subject=auth.identity.subject, due_at=due_at)
        self.repository.save_commitment(item)
        return item

    def activate_commitment(self, auth: AuthorizationContext, commitment_id: str) -> Commitment:
        self._authorize(auth, Capability.COMMITMENT_UPDATE)
        item = self.repository.get_commitment(commitment_id)
        if item is None:
            raise ResolutionNotFoundError(commitment_id)
        self._tenant(auth, item.tenant_id)
        if item.status != CommitmentStatus.PENDING:
            raise InvalidResolutionTransition("Only pending commitments can be activated")
        item.status = CommitmentStatus.ACTIVE
        self.repository.save_commitment(item)
        return item

    def record_outcome(self, auth: AuthorizationContext, *, commitment_id: str, summary: str,
                       status: OutcomeStatus, evidence_ids: Optional[list[str]] = None) -> Outcome:
        self._authorize(auth, Capability.OUTCOME_RECORD)
        commitment = self.repository.get_commitment(commitment_id)
        if commitment is None:
            raise ResolutionNotFoundError(commitment_id)
        self._tenant(auth, commitment.tenant_id)
        if commitment.status != CommitmentStatus.ACTIVE:
            raise InvalidResolutionTransition("An outcome can only be recorded for an active commitment")
        if not summary.strip():
            raise InvalidResolutionTransition("Outcome summary is required")
        item = new_outcome(case_id=commitment.case_id, tenant_id=commitment.tenant_id, commitment_id=commitment.id,
                           summary=summary.strip(), status=status, recorded_by_subject=auth.identity.subject,
                           evidence_ids=evidence_ids)
        self.repository.save_outcome(item)
        return item

    def verify_outcome(self, auth: AuthorizationContext, outcome_id: str) -> Outcome:
        self._authorize(auth, Capability.OUTCOME_VERIFY)
        item = self.repository.get_outcome(outcome_id)
        if item is None:
            raise ResolutionNotFoundError(outcome_id)
        self._tenant(auth, item.tenant_id)
        if item.status not in {OutcomeStatus.ACHIEVED, OutcomeStatus.PARTIAL, OutcomeStatus.NOT_ACHIEVED}:
            raise InvalidResolutionTransition("Only recorded outcomes can be verified")
        if not item.evidence_ids:
            raise InvalidResolutionTransition("Outcome verification requires evidence")
        item.status = OutcomeStatus.VERIFIED
        self.repository.save_outcome(item)
        commitment = self.repository.get_commitment(item.commitment_id)
        if commitment is not None:
            commitment.status = CommitmentStatus.COMPLETED
            self.repository.save_commitment(commitment)
        return item
