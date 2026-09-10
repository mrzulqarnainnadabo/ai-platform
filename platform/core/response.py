"""ModelResponse, TokenUsage, and FinishReason Contracts for AI Platform Kernel."""

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from platform.core.messages import Message, Role


class FinishReason(str, Enum):
    """Reason for completion termination."""
    STOP = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class TokenUsage:
    """Standardized token consumption and cost metadata."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: Optional[float] = None

    def __post_init__(self) -> None:
        if self.total_tokens == 0 and (self.prompt_tokens > 0 or self.completion_tokens > 0):
            self.total_tokens = self.prompt_tokens + self.completion_tokens

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": self.cost_usd,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenUsage":
        return cls(
            prompt_tokens=data.get("prompt_tokens", 0),
            completion_tokens=data.get("completion_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
            cost_usd=data.get("cost_usd"),
        )


@dataclass
class ModelResponse:
    """Provider-neutral model execution response."""

    message: Message
    finish_reason: FinishReason
    usage: TokenUsage
    model_name: str
    provider_name: str
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)
    structured_output: Optional[Dict[str, Any]] = None
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "response_id": self.response_id,
            "created_at": self.created_at,
            "model_name": self.model_name,
            "provider_name": self.provider_name,
            "finish_reason": self.finish_reason.value if isinstance(self.finish_reason, FinishReason) else str(self.finish_reason),
            "message": self.message.to_dict(),
            "usage": self.usage.to_dict(),
            "raw_metadata": self.raw_metadata,
        }
        if self.structured_output is not None:
            res["structured_output"] = self.structured_output
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelResponse":
        fr_raw = data.get("finish_reason", "stop")
        fr = FinishReason(fr_raw) if fr_raw in [e.value for e in FinishReason] else FinishReason.STOP

        msg_data = data.get("message", {})
        msg = Message.from_dict(msg_data) if isinstance(msg_data, dict) else Message(role=Role.ASSISTANT, content="")

        usage_data = data.get("usage", {})
        usage = TokenUsage.from_dict(usage_data) if isinstance(usage_data, dict) else TokenUsage()

        return cls(
            response_id=data.get("response_id", str(uuid.uuid4())),
            created_at=data.get("created_at", time.time()),
            model_name=data.get("model_name", "unknown"),
            provider_name=data.get("provider_name", "unknown"),
            finish_reason=fr,
            message=msg,
            usage=usage,
            structured_output=data.get("structured_output"),
            raw_metadata=data.get("raw_metadata", {}),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ModelResponse":
        return cls.from_dict(json.loads(json_str))
