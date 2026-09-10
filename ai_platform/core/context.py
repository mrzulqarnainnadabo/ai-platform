"""Execution Context and Cancellation Token Contracts for AI Platform Kernel."""

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from ai_platform.core.errors import ProviderTimeoutError


class CancellationToken:
    """Thread-safe cancellation token for model generation and execution loops."""

    def __init__(self) -> None:
        self._is_cancelled: bool = False
        self._reason: str = "Execution cancelled"

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled

    @property
    def reason(self) -> str:
        return self._reason

    def cancel(self, reason: str = "Execution cancelled") -> None:
        if not reason or not isinstance(reason, str):
            reason = "Execution cancelled"
        self._is_cancelled = True
        self._reason = reason

    def raise_if_cancelled(self) -> None:
        if self._is_cancelled:
            raise ProviderTimeoutError(message=f"Request cancelled: {self._reason}")


@dataclass
class ExecutionContext:
    """Carries request identity, timeout, cancellation state, and trace metadata."""

    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = "default"
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    timeout_seconds: float = 60.0
    cancellation_token: CancellationToken = field(default_factory=CancellationToken)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.timeout_seconds, (int, float)) or self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be a positive number")
        if not self.tenant_id or not isinstance(self.tenant_id, str):
            raise ValueError("tenant_id must be a non-empty string")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "timeout_seconds": self.timeout_seconds,
            "is_cancelled": self.cancellation_token.is_cancelled,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionContext":
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        token = CancellationToken()
        if data.get("is_cancelled"):
            token.cancel()
        return cls(
            trace_id=data.get("trace_id", str(uuid.uuid4())),
            tenant_id=data.get("tenant_id", "default"),
            user_id=data.get("user_id"),
            agent_id=data.get("agent_id"),
            timeout_seconds=float(data.get("timeout_seconds", 60.0)),
            cancellation_token=token,
            metadata=data.get("metadata", {}) if isinstance(data.get("metadata"), dict) else {},
        )
