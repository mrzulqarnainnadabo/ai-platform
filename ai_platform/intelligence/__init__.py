"""First-party intelligence domain for governed problem resolution."""

from .ingestion import EvidenceIngestionPort, IngestExtract, IngestMediaType, IngestRequest, PassthroughTextIngestion
from .models import Assertion, AssertionKind, AuditEvent, Case, CaseStatus, Evidence, EvidenceSourceType
from .repository import InMemoryCaseRepository
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
]
