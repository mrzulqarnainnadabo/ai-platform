"""ModelResponse, TokenUsage, and FinishReason Contracts for AI Platform Kernel."""

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from ai_platform.core.messages import Message, Role


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
        if not isinstance(self.prompt_tokens, int) or self.prompt_tokens < 0:
            raise ValueError("prompt_tokens must be a non-negative integer")
        if not isinstance(self.completion_tokens, int) or self.completion_tokens < 0:
            raise ValueError("completion_tokens must be a non-negative integer")
        if not isinstance(self.total_tokens, int) or self.total_tokens < 0:
            raise ValueError("total_tokens must be a non-negative integer")
        if self.cost_usd is not None and (not isinstance(self.cost_usd, (int, float)) or self.cost_usd < 0.0):
            raise ValueError("cost_usd must be a non-negative number")

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
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        return cls(
            prompt_tokens=int(data.get("prompt_tokens", 0)),
            completion_tokens=int(data.get("completion_tokens", 0)),
            total_tokens=int(data.get("total_tokens", 0)),
            cost_usd=float(data["cost_usd"]) if data.get("cost_usd") is not None else None,
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

    def __post_init__(self) -> None:
        if not isinstance(self.message, Message):
            raise ValueError("message must be an instance of Message")
        if isinstance(self.finish_reason, str):
            valid_reasons = [e.value for e in FinishReason]
            if self.finish_reason not in valid_reasons:
                raise ValueError(f"Invalid finish_reason '{self.finish_reason}'. Must be one of {valid_reasons}")
            self.finish_reason = FinishReason(self.finish_reason)
        elif not isinstance(self.finish_reason, FinishReason):
            raise ValueError(f"finish_reason must be FinishReason or valid string, got {type(self.finish_reason)}")

        if not isinstance(self.usage, TokenUsage):
            raise ValueError("usage must be an instance of TokenUsage")
        if not self.model_name or not isinstance(self.model_name, str):
            raise ValueError("model_name must be a non-empty string")
        if not self.provider_name or not isinstance(self.provider_name, str):
            raise ValueError("provider_name must be a non-empty string")

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "response_id": self.response_id,
            "created_at": self.created_at,
            "model_name": self.model_name,
            "provider_name": self.provider_name,
            "finish_reason": self.finish_reason.value,
            "message": self.message.to_dict(),
            "usage": self.usage.to_dict(),
            "raw_metadata": self.raw_metadata,
        }
        if self.structured_output is not None:
            res["structured_output"] = self.structured_output
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelResponse":
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        fr_raw = data.get("finish_reason")
        valid_reasons = [e.value for e in FinishReason]
        if not fr_raw or fr_raw not in valid_reasons:
            raise ValueError(f"Invalid or missing finish_reason '{fr_raw}'. Must be one of {valid_reasons}")
        fr = FinishReason(fr_raw)

        msg_data = data.get("message")
        if not isinstance(msg_data, dict):
            raise ValueError("ModelResponse dictionary must contain 'message' dict")
        msg = Message.from_dict(msg_data)

        usage_data = data.get("usage", {})
        usage = TokenUsage.from_dict(usage_data) if isinstance(usage_data, dict) else TokenUsage()

        m_name = data.get("model_name")
        p_name = data.get("provider_name")
        if not m_name or not isinstance(m_name, str):
            raise ValueError("ModelResponse dictionary must contain non-empty 'model_name'")
        if not p_name or not isinstance(p_name, str):
            raise ValueError("ModelResponse dictionary must contain non-empty 'provider_name'")

        return cls(
            response_id=str(data.get("response_id", str(uuid.uuid4()))),
            created_at=float(data.get("created_at", time.time())),
            model_name=m_name,
            provider_name=p_name,
            finish_reason=fr,
            message=msg,
            usage=usage,
            structured_output=data.get("structured_output"),
            raw_metadata=data.get("raw_metadata", {}) if isinstance(data.get("raw_metadata"), dict) else {},
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ModelResponse":
        if not isinstance(json_str, str):
            raise ValueError("json_str must be a string")
        return cls.from_dict(json.loads(json_str))
