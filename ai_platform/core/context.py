"""Execution context and cooperative cancellation contracts."""
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from ai_platform.core.errors import CancellationError


class CancellationToken:
    def __init__(self) -> None:
        self._is_cancelled = False
        self._reason = "Execution cancelled"

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled

    @property
    def reason(self) -> str:
        return self._reason

    def cancel(self, reason: str = "Execution cancelled") -> None:
        self._is_cancelled = True
        self._reason = reason if isinstance(reason, str) and reason else "Execution cancelled"

    def raise_if_cancelled(self) -> None:
        if self._is_cancelled:
            raise CancellationError(message=f"Request cancelled: {self._reason}")


@dataclass
class ExecutionContext:
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = "default"
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    timeout_seconds: float = 60.0
    cancellation_token: CancellationToken = field(default_factory=CancellationToken)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.trace_id, str) or not self.trace_id:
            raise ValueError("trace_id must be a non-empty string")
        if not isinstance(self.tenant_id, str) or not self.tenant_id:
            raise ValueError("tenant_id must be a non-empty string")
        if not isinstance(self.timeout_seconds, (int, float)) or self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if not isinstance(self.cancellation_token, CancellationToken):
            raise ValueError("cancellation_token must be CancellationToken")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")

    def to_dict(self) -> Dict[str, Any]:
        return {"trace_id": self.trace_id, "tenant_id": self.tenant_id,
                "user_id": self.user_id, "agent_id": self.agent_id,
                "timeout_seconds": self.timeout_seconds,
                "is_cancelled": self.cancellation_token.is_cancelled,
                "metadata": self.metadata}
