"""First-party intelligence domain for governed problem resolution."""

from .ingestion import EvidenceIngestionPort, IngestExtract, IngestMediaType, IngestRequest, PassthroughTextIngestion
from .models import Assertion, AssertionKind, AuditEvent, Case, CaseStatus, Evidence, EvidenceSourceType
from .repository import InMemoryCaseRepository
from .resolution import (
    ActionProposal,
    ActionProposalStatus,
    Commitment,
    CommitmentStatus,
    Outcome,
    OutcomeStatus,
    Responsibility,
)
from .resolution_repository import InMemoryResolutionRepository
from .resolution_service import InvalidResolutionTransition, ResolutionNotFoundError, ResolutionService
from .service import CaseService, EvidenceService

__all__ = [
    "Assertion",
    "AssertionKind",
    "AuditEvent",
    "Case",
    "CaseService",
    "CaseStatus",
    "Evidence",
    "EvidenceIngestionPort",
    "EvidenceService",
    "EvidenceSourceType",
    "InMemoryCaseRepository",
    "IngestExtract",
    "IngestMediaType",
    "IngestRequest",
    "PassthroughTextIngestion",
    "Responsibility",
    "ActionProposal",
    "ActionProposalStatus",
    "Commitment",
    "CommitmentStatus",
    "Outcome",
    "OutcomeStatus",
    "InMemoryResolutionRepository",
    "InvalidResolutionTransition",
    "ResolutionNotFoundError",
    "ResolutionService",
]
