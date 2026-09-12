"""Supabase/Postgres-backed CaseRepository (server-side only).

Requires a constrained server credential (service role or equivalent).
Never use this module from browser code.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Mapping, Optional

from .models import (
    Assertion,
    AssertionKind,
    AuditEvent,
    Case,
    CaseStatus,
    Evidence,
    EvidenceSourceType,
)


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    raise TypeError("invalid timestamp")


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return list(value)


def _case_from_row(r: Mapping[str, Any]) -> Case:
    return Case(
        id=str(r["id"]),
        tenant_id=str(r["tenant_id"]),
        created_by_subject=str(r["created_by_subject"]),
        title=str(r["title"]),
        summary=str(r["summary"]),
        status=CaseStatus(str(r["status"])),
        created_at=_parse_dt(r["created_at"]),
        updated_at=_parse_dt(r["updated_at"]),
        missing_evidence_questions=[str(x) for x in _as_list(r.get("missing_evidence_questions"))],
    )


class SupabaseCaseRepository:
    """Maps domain objects to ai_platform_* tables from migration 0003."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def _tenant_for_case(self, case_id: str) -> str:
        row = (
            self._client.table("ai_platform_cases")
            .select("tenant_id")
            .eq("id", case_id)
            .limit(1)
            .execute()
        )
        data = getattr(row, "data", None) or []
        if not data:
            raise LookupError(f"case not found: {case_id}")
        return str(data[0]["tenant_id"])

    def save_case(self, case: Case) -> None:
        payload = {
            "id": case.id,
            "tenant_id": case.tenant_id,
            "created_by_subject": case.created_by_subject,
            "title": case.title,
            "summary": case.summary,
            "status": case.status.value,
            "missing_evidence_questions": case.missing_evidence_questions,
            "created_at": case.created_at.isoformat(),
            "updated_at": case.updated_at.isoformat(),
        }
        self._client.table("ai_platform_cases").upsert(payload).execute()

    def get_case(self, case_id: str) -> Case | None:
        row = (
            self._client.table("ai_platform_cases")
            .select("*")
            .eq("id", case_id)
            .limit(1)
            .execute()
        )
        data = getattr(row, "data", None) or []
        if not data:
            return None
        return _case_from_row(data[0])

    def list_cases(self, tenant_id: str) -> list[Case]:
        row = (
            self._client.table("ai_platform_cases")
            .select("*")
            .eq("tenant_id", tenant_id)
            .order("updated_at", desc=True)
            .execute()
        )
        data = getattr(row, "data", None) or []
        return [_case_from_row(r) for r in data]

    def save_assertion(self, assertion: Assertion) -> None:
        tenant_id = self._tenant_for_case(assertion.case_id)
        payload = {
            "id": assertion.id,
            "case_id": assertion.case_id,
            "tenant_id": tenant_id,
            "text": assertion.text,
            "kind": assertion.kind.value,
            "created_by": assertion.created_by,
            "requires_evidence": assertion.requires_evidence,
            "evidence_ids": assertion.evidence_ids,
            "created_at": assertion.created_at.isoformat(),
        }
        self._client.table("ai_platform_assertions").upsert(payload).execute()

    def list_assertions(self, case_id: str) -> list[Assertion]:
        row = (
            self._client.table("ai_platform_assertions")
            .select("*")
            .eq("case_id", case_id)
            .execute()
        )
        data = getattr(row, "data", None) or []
        out: list[Assertion] = []
        for r in data:
            out.append(
                Assertion(
                    id=str(r["id"]),
                    case_id=str(r["case_id"]),
                    text=str(r["text"]),
                    kind=AssertionKind(str(r["kind"])),
                    created_by=str(r["created_by"]),
                    requires_evidence=bool(r["requires_evidence"]),
                    created_at=_parse_dt(r["created_at"]),
                    evidence_ids=[str(x) for x in _as_list(r.get("evidence_ids"))],
                )
            )
        return out

    def save_evidence(self, evidence: Evidence) -> None:
        tenant_id = self._tenant_for_case(evidence.case_id)
        payload = {
            "id": evidence.id,
            "case_id": evidence.case_id,
            "tenant_id": tenant_id,
            "assertion_id": evidence.assertion_id,
            "body": evidence.body,
            "source_type": evidence.source_type.value,
            "source_uri": evidence.source_uri,
            "note": evidence.note,
            "created_by_subject": evidence.created_by_subject,
            "created_at": evidence.created_at.isoformat(),
        }
        self._client.table("ai_platform_evidence").upsert(payload).execute()

    def list_evidence(self, case_id: str) -> list[Evidence]:
        row = (
            self._client.table("ai_platform_evidence")
            .select("*")
            .eq("case_id", case_id)
            .execute()
        )
        data = getattr(row, "data", None) or []
        out: list[Evidence] = []
        for r in data:
            out.append(
                Evidence(
                    id=str(r["id"]),
                    case_id=str(r["case_id"]),
                    assertion_id=str(r["assertion_id"]) if r.get("assertion_id") else None,
                    body=str(r["body"]),
                    source_type=EvidenceSourceType(str(r["source_type"])),
                    source_uri=str(r["source_uri"]) if r.get("source_uri") else None,
                    note=str(r["note"]) if r.get("note") else None,
                    created_by_subject=str(r["created_by_subject"]),
                    created_at=_parse_dt(r["created_at"]),
                )
            )
        return out

    def save_audit(self, event: AuditEvent) -> None:
        payload = {
            "id": event.id,
            "tenant_id": event.tenant_id,
            "actor_subject": event.actor_subject,
            "action": event.action,
            "object_type": event.object_type,
            "object_id": event.object_id,
            "payload_digest": event.payload_digest,
            "metadata": dict(event.metadata),
            "created_at": event.created_at.isoformat(),
        }
        self._client.table("ai_platform_audit_events").insert(payload).execute()

    def list_audit(self, object_id: str, tenant_id: str | None = None) -> list[AuditEvent]:
        query = (
            self._client.table("ai_platform_audit_events")
            .select("*")
            .eq("object_id", object_id)
        )
        if tenant_id is not None:
            query = query.eq("tenant_id", tenant_id)
        row = query.execute()
        data = getattr(row, "data", None) or []
        out: list[AuditEvent] = []
        for r in data:
            meta = r.get("metadata") or {}
            if isinstance(meta, str):
                meta = json.loads(meta)
            out.append(
                AuditEvent(
                    id=str(r["id"]),
                    tenant_id=str(r["tenant_id"]),
                    actor_subject=str(r["actor_subject"]),
                    action=str(r["action"]),
                    object_type=str(r["object_type"]),
                    object_id=str(r["object_id"]),
                    payload_digest=str(r["payload_digest"]),
                    metadata=dict(meta) if isinstance(meta, Mapping) else {},
                    created_at=_parse_dt(r["created_at"]),
                )
            )
        return out
