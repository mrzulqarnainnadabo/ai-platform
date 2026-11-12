from datetime import datetime, timezone

import pytest

from ai_platform.intelligence.resolution import ActionProposalStatus, CommitmentStatus, OutcomeStatus
from ai_platform.intelligence.resolution_repository import InMemoryResolutionRepository
from ai_platform.intelligence.resolution_service import InvalidResolutionTransition, ResolutionService
from ai_platform.policy.authorization import AuthorizationContext, Identity, Permissions
from ai_platform.policy.capabilities import Capability
from ai_platform.policy.errors import PolicyDeniedError


def auth(*capabilities: Capability, tenant: str = "tenant-a", subject: str = "user-a") -> AuthorizationContext:
    return AuthorizationContext(
        identity=Identity(subject=subject, tenant_id=tenant),
        permissions=Permissions(capabilities=frozenset(capabilities)),
    )


ALL = tuple(Capability)


def test_full_resolution_lifecycle_requires_approval_and_evidence():
    service = ResolutionService(InMemoryResolutionRepository())
    context = auth(*ALL)

    responsibility = service.propose_responsibility(
        context, case_id="case-1", subject="agency-a", role="operator", scope="repair road",
    )
    proposal = service.propose_action(
        context, case_id="case-1", title="Repair", description="Repair the reported road segment",
        responsibility_id=responsibility.id,
    )

    with pytest.raises(InvalidResolutionTransition):
        service.create_commitment(context, proposal_id=proposal.id, owner_subject="agency-a", action="repair")

    proposal = service.submit_action(context, proposal.id)
    assert proposal.status == ActionProposalStatus.SUBMITTED
    proposal = service.approve_action(context, proposal.id)
    assert proposal.status == ActionProposalStatus.APPROVED

    commitment = service.create_commitment(
        context, proposal_id=proposal.id, owner_subject="agency-a", action="repair",
        due_at=datetime.now(timezone.utc),
    )
    assert commitment.status == CommitmentStatus.PENDING
    commitment = service.activate_commitment(context, commitment.id)

    outcome = service.record_outcome(
        context, commitment_id=commitment.id, summary="Repair completed",
        status=OutcomeStatus.ACHIEVED, evidence_ids=["evidence-1"],
    )
    verified = service.verify_outcome(context, outcome.id)
    assert verified.status == OutcomeStatus.VERIFIED
    assert service.repository.get_commitment(commitment.id).status == CommitmentStatus.COMPLETED


def test_outcome_verification_fails_without_evidence():
    service = ResolutionService(InMemoryResolutionRepository())
    context = auth(*ALL)
    proposal = service.propose_action(context, case_id="case-1", title="Fix", description="Fix it")
    service.submit_action(context, proposal.id)
    proposal = service.approve_action(context, proposal.id)
    commitment = service.create_commitment(context, proposal_id=proposal.id, owner_subject="agency-a", action="fix")
    commitment = service.activate_commitment(context, commitment.id)
    outcome = service.record_outcome(
        context, commitment_id=commitment.id, summary="Claimed complete", status=OutcomeStatus.ACHIEVED,
    )
    with pytest.raises(InvalidResolutionTransition, match="requires evidence"):
        service.verify_outcome(context, outcome.id)


def test_cross_tenant_mutation_is_denied():
    service = ResolutionService(InMemoryResolutionRepository())
    owner = auth(*ALL, tenant="tenant-a")
    other = auth(*ALL, tenant="tenant-b")
    proposal = service.propose_action(owner, case_id="case-1", title="Fix", description="Fix it")
    with pytest.raises(PolicyDeniedError):
        service.submit_action(other, proposal.id)


def test_missing_capability_fails_closed():
    service = ResolutionService(InMemoryResolutionRepository())
    with pytest.raises(PolicyDeniedError):
        service.propose_action(auth(Capability.CASE_READ), case_id="case-1", title="Fix", description="Fix it")
