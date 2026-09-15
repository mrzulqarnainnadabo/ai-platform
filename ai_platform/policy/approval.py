from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .capabilities import Capability
from .authorization import Identity
from .errors import HumanApprovalRequiredError


@dataclass(frozen=True)
class HumanApproval:
    """Compatibility proof scoped to a tenant, subject and capability."""
    subject: str
    capability: Capability
    approval_id: str
    approver_id: str
    tenant_id: str = "default"

    def matches(self, identity: Identity, capability: Capability) -> bool:
        return (
            self.tenant_id == identity.tenant_id
            and self.subject == identity.subject
            and self.capability == capability
            and bool(self.approval_id)
            and bool(self.approver_id)
        )


class ApprovalService:
    """Durable human-approval service backed by Supabase."""

    def __init__(self, client: Any) -> None:
        self.client = client

    def request(self, *, tenant_id: str, subject_id: str, capability: str,
                run_id: str | None = None, expires_at: datetime | None = None,
                metadata: dict | None = None) -> str:
        approval_id = str(uuid4())
        self.client.table("ai_platform_approvals").insert({
            "id": approval_id,
            "tenant_id": tenant_id,
            "subject_id": subject_id,
            "capability": capability,
            "run_id": run_id,
            "status": "pending",
            "expires_at": expires_at.isoformat() if expires_at else None,
            "metadata": metadata or {},
        }).execute()
        return approval_id

    def decide(self, *, approval_id: str, tenant_id: str, approver_id: str,
               decision: str) -> None:
        if decision not in {"approved", "rejected"}:
            raise ValueError("decision must be approved or rejected")
        result = self.client.table("ai_platform_approvals").update({
            "status": decision,
            "approver_id": approver_id,
            "decided_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", approval_id).eq("tenant_id", tenant_id).eq("status", "pending").execute()
        if not getattr(result, "data", None):
            raise HumanApprovalRequiredError("Approval is missing, expired, or already decided")

    def get(self, *, approval_id: str, tenant_id: str, subject_id: str, capability: str) -> HumanApproval | None:
        row = self.client.table("ai_platform_approvals").select("*").eq("id", approval_id).eq("tenant_id", tenant_id).eq("subject_id", subject_id).limit(1).execute()
        data = getattr(row, "data", None) or []
        if not data:
            return None
        item = data[0]
        if item.get("status") != "approved":
            return None
        expires = item.get("expires_at")
        if expires and datetime.fromisoformat(str(expires).replace("Z", "+00:00")) <= datetime.now(timezone.utc):
            self.client.table("ai_platform_approvals").update({"status": "expired"}).eq("id", approval_id).eq("tenant_id", tenant_id).execute()
            return None
        return HumanApproval(
            subject=subject_id,
            capability=Capability(capability),
            approval_id=approval_id,
            approver_id=str(item.get("approver_id") or ""),
            tenant_id=tenant_id,
        )
