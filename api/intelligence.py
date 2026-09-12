"""Authenticated case-intake API."""
from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ai_platform.intelligence.models import CaseAggregate, EvidenceSourceType
from ai_platform.intelligence.service import CaseNotFoundError, CaseService, EvidenceService, InvalidCaseInput
from ai_platform.intelligence.store import get_case_repository
from ai_platform.policy.authorization import AuthorizationContext
from ai_platform.policy.capabilities import Capability
from ai_platform.policy.errors import PolicyDeniedError
from ai_platform.runtime.authorized import AuthorizedModelRuntime
from api.dependencies import require_auth, require_runtime

router = APIRouter(prefix="/api/v1/cases", tags=["cases"])
_repository = get_case_repository()
_case_service = CaseService(_repository)
_evidence_service = EvidenceService(_repository)


class CaseCreateRequest(BaseModel):
    summary: str = Field(..., min_length=1, max_length=10000)
    title: Optional[str] = Field(default=None, max_length=200)


class EvidenceAttachRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=50000)
    source_type: EvidenceSourceType
    source_uri: Optional[str] = Field(default=None, max_length=4000)
    note: Optional[str] = Field(default=None, max_length=4000)
    assertion_id: Optional[str] = None


def _iso(value: datetime) -> str:
    return value.isoformat()


def _aggregate_response(aggregate: CaseAggregate) -> dict:
    return {
        "case": {
            "id": aggregate.case.id,
            "tenant_id": aggregate.case.tenant_id,
            "created_by_subject": aggregate.case.created_by_subject,
            "title": aggregate.case.title,
            "summary": aggregate.case.summary,
            "status": aggregate.case.status.value,
            "created_at": _iso(aggregate.case.created_at),
            "updated_at": _iso(aggregate.case.updated_at),
        },
        "assertions": [
            {"id": x.id, "case_id": x.case_id, "text": x.text, "kind": x.kind.value,
             "created_by": x.created_by, "requires_evidence": x.requires_evidence,
             "created_at": _iso(x.created_at), "evidence_ids": x.evidence_ids}
            for x in aggregate.assertions
        ],
        "evidence": [
            {"id": x.id, "case_id": x.case_id, "assertion_id": x.assertion_id, "body": x.body,
             "source_type": x.source_type.value, "source_uri": x.source_uri, "note": x.note,
             "created_by_subject": x.created_by_subject, "created_at": _iso(x.created_at)}
            for x in aggregate.evidence
        ],
        "missing_evidence_questions": aggregate.missing_evidence_questions,
        "audit_events": [
            {"id": x.id, "tenant_id": x.tenant_id, "actor_subject": x.actor_subject,
             "action": x.action, "object_type": x.object_type, "object_id": x.object_id,
             "payload_digest": x.payload_digest, "metadata": x.metadata, "created_at": _iso(x.created_at)}
            for x in aggregate.audit_events
        ],
    }


def _raise(exc: Exception) -> HTTPException:
    if isinstance(exc, PolicyDeniedError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Capability denied")
    if isinstance(exc, CaseNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if isinstance(exc, (InvalidCaseInput, ValueError)):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Case operation failed")


@router.post("")
async def create_case(request: CaseCreateRequest, auth: AuthorizationContext = Depends(require_auth)) -> dict:
    try:
        return _aggregate_response(_case_service.get(auth, _case_service.create(auth, request.summary, request.title).id))
    except Exception as exc:
        raise _raise(exc) from exc


@router.get("/{case_id}")
async def get_case(case_id: str, auth: AuthorizationContext = Depends(require_auth)) -> dict:
    try:
        return _aggregate_response(_case_service.get(auth, case_id))
    except Exception as exc:
        raise _raise(exc) from exc


@router.post("/{case_id}/triage")
async def triage_case(case_id: str, auth: AuthorizationContext = Depends(require_auth)) -> dict:
    try:
        # Authorize before resolving provider configuration so a denied request
        # deterministically returns 403 and cannot trigger model work.
        _case_service.authorize(auth, Capability.CASE_TRIAGE)
        runtime: AuthorizedModelRuntime = require_runtime()
        model_name = (os.getenv("AI_PLATFORM_TRIAGE_MODEL") or "gpt-4o-mini").strip()
        return _aggregate_response(await _case_service.triage(auth, case_id, runtime, model_name=model_name))
    except HTTPException:
        raise
    except Exception as exc:
        raise _raise(exc) from exc


@router.post("/{case_id}/evidence")
async def attach_evidence(case_id: str, request: EvidenceAttachRequest,
                          auth: AuthorizationContext = Depends(require_auth)) -> dict:
    try:
        evidence = _evidence_service.attach(
            auth, case_id, body=request.body, source_type=request.source_type,
            source_uri=request.source_uri, note=request.note, assertion_id=request.assertion_id,
        )
        return {
            "id": evidence.id,
            "case_id": evidence.case_id,
            "assertion_id": evidence.assertion_id,
            "body": evidence.body,
            "source_type": evidence.source_type.value,
            "source_uri": evidence.source_uri,
            "note": evidence.note,
            "created_by_subject": evidence.created_by_subject,
            "created_at": _iso(evidence.created_at),
        }
    except Exception as exc:
        raise _raise(exc) from exc
