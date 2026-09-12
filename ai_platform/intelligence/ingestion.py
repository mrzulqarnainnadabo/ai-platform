"""Evidence ingestion ports — first-party interfaces only.

Adapters for URL fetch, PDF/DOCX parse, OCR, ASR, or media extraction belong
*outside* this module and must never receive provider API keys from the client.

This vertical slice does not implement adapters. Production code may later
register implementations while keeping Case/Evidence provenance rules intact.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Protocol


class IngestMediaType(str, Enum):
    TEXT = "text"
    URL = "url"
    PDF = "pdf"
    DOCX = "docx"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


@dataclass(frozen=True)
class IngestRequest:
    """Untrusted user-supplied material to be turned into Evidence candidates."""

    media_type: IngestMediaType
    # Exactly one of the following should be populated by the caller.
    text: Optional[str] = None
    source_uri: Optional[str] = None
    # Opaque storage key for blobs already accepted by the host (not raw bytes in domain).
    blob_ref: Optional[str] = None
    content_type: Optional[str] = None
    note: Optional[str] = None


@dataclass(frozen=True)
class IngestExtract:
    """Normalized text (or structured fields) extracted from a source."""

    body: str
    source_type_hint: str  # maps to EvidenceSourceType values at the service boundary
    source_uri: Optional[str]
    confidence: float
    extractor: str  # e.g. "passthrough", "pdf-adapter", "whisper-adapter"


class EvidenceIngestionPort(Protocol):
    """Host-facing port. Implementations live in integrations/, not intelligence core."""

    def extract(self, request: IngestRequest) -> IngestExtract:
        """Return extracted text with provenance hints. Must not call model providers."""
        ...


class PassthroughTextIngestion:
    """Minimal adapter: accepts user_text only. Safe default for tests and v1 API."""

    def extract(self, request: IngestRequest) -> IngestExtract:
        if request.media_type != IngestMediaType.TEXT or not (request.text or "").strip():
            raise ValueError("PassthroughTextIngestion only accepts non-empty text")
        return IngestExtract(
            body=request.text.strip(),
            source_type_hint="user_text",
            source_uri=None,
            confidence=1.0,
            extractor="passthrough",
        )
