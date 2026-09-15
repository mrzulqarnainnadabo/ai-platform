"""Message and provider-neutral request contracts for the AI Platform kernel."""

import base64
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class ProviderOptions(BaseModel):
    """Validated provider-neutral knobs; there is deliberately no arbitrary dict."""

    model_config = ConfigDict(extra="forbid")

    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    seed: Optional[int] = Field(default=None, ge=0)
    logprobs: Optional[bool] = None
    top_logprobs: Optional[int] = Field(default=None, ge=0, le=20)
    reasoning_effort: Optional[str] = Field(default=None, pattern=r"^(low|medium|high)$")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class Role(str, Enum):
    SYSTEM = "system"
    DEVELOPER = "developer"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class ContentPart:
    type: str
    text: Optional[str] = None
    image_url: Optional[str] = None
    data: Optional[bytes] = None
    mime_type: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.type or not isinstance(self.type, str):
            raise ValueError("ContentPart type must be a non-empty string")
        if self.data is not None and not isinstance(self.data, bytes):
            raise ValueError("data must be bytes if provided")

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {"type": self.type}
        if self.text is not None: res["text"] = self.text
        if self.image_url is not None: res["image_url"] = self.image_url
        if self.data is not None: res["data_b64"] = base64.b64encode(self.data).decode("utf-8")
        if self.mime_type is not None: res["mime_type"] = self.mime_type
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContentPart":
        if not isinstance(data, dict): raise ValueError("Data must be a dictionary")
        raw_b64 = data.get("data_b64")
        return cls(type=str(data.get("type", "text")), text=data.get("text"), image_url=data.get("image_url"),
                   data=base64.b64decode(raw_b64.encode("utf-8")) if isinstance(raw_b64, str) and raw_b64 else None,
                   mime_type=data.get("mime_type"))


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: Dict[str, Any]

    def __post_init__(self) -> None:
        if not self.id or not isinstance(self.id, str): raise ValueError("ToolCall id must be a non-empty string")
        if not self.name or not isinstance(self.name, str): raise ValueError("ToolCall name must be a non-empty string")
        if not isinstance(self.arguments, dict): raise ValueError("ToolCall arguments must be a dictionary")

    def to_dict(self) -> Dict[str, Any]: return {"id": self.id, "name": self.name, "arguments": self.arguments}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCall":
        args = data.get("arguments", {})
        if isinstance(args, str):
            try: args = json.loads(args)
            except Exception: args = {"raw": args}
        return cls(id=str(data.get("id", "")), name=str(data.get("name", "")), arguments=args if isinstance(args, dict) else {})


@dataclass
class ToolResult:
    tool_call_id: str
    content: str
    is_error: bool = False

    def __post_init__(self) -> None:
        if not self.tool_call_id or not isinstance(self.tool_call_id, str): raise ValueError("tool_call_id must be a non-empty string")
        if self.content is None: raise ValueError("content cannot be None")

    def to_dict(self) -> Dict[str, Any]: return {"tool_call_id": self.tool_call_id, "content": self.content, "is_error": self.is_error}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolResult":
        if not data.get("tool_call_id"): raise ValueError("ToolResult dictionary must contain non-empty 'tool_call_id'")
        return cls(tool_call_id=str(data["tool_call_id"]), content=str(data.get("content", "")), is_error=bool(data.get("is_error", False)))


@dataclass
class Message:
    role: Role
    content: Union[str, List[ContentPart]]
    name: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.role, str):
            if self.role not in [e.value for e in Role]: raise ValueError(f"Invalid message role '{self.role}'")
            self.role = Role(self.role)
        elif not isinstance(self.role, Role):
            raise ValueError("role must be Role or a valid role string")
        if self.content is None: raise ValueError("Message content cannot be None")
        if isinstance(self.content, list) and any(not isinstance(p, ContentPart) for p in self.content):
            raise ValueError("All elements of content list must be ContentPart instances")

    def get_text_content(self) -> str:
        if isinstance(self.content, str): return self.content
        return " ".join(part.text for part in self.content if part.text)

    def to_dict(self) -> Dict[str, Any]:
        c_val = self.content if isinstance(self.content, str) else [p.to_dict() for p in self.content]
        result: Dict[str, Any] = {"role": self.role.value, "content": c_val}
        if self.name is not None: result["name"] = self.name
        if self.tool_calls is not None: result["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]
        if self.tool_call_id is not None: result["tool_call_id"] = self.tool_call_id
        if self.metadata: result["metadata"] = self.metadata
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        role_raw = data.get("role")
        if not isinstance(role_raw, str) or role_raw not in [e.value for e in Role]: raise ValueError("Message dictionary must contain a valid 'role'")
        content_raw = data.get("content")
        if content_raw is None: raise ValueError("Message dictionary must contain 'content'")
        content = [ContentPart.from_dict(p) for p in content_raw if isinstance(p, dict)] if isinstance(content_raw, list) else str(content_raw)
        tc_raw = data.get("tool_calls")
        tool_calls = [ToolCall.from_dict(tc) for tc in tc_raw if isinstance(tc, dict)] if isinstance(tc_raw, list) else None
        return cls(role=Role(role_raw), content=content, name=data.get("name"), tool_calls=tool_calls,
                   tool_call_id=data.get("tool_call_id"), metadata=data.get("metadata", {}) if isinstance(data.get("metadata"), dict) else {})

    def to_json(self) -> str: return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Message": return cls.from_dict(json.loads(json_str))
