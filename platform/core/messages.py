"""Message, Role, ContentPart, ToolCall, and ToolResult Contracts for AI Platform Kernel."""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class Role(str, Enum):
    """Standardized conversation message roles."""
    SYSTEM = "system"
    DEVELOPER = "developer"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class ContentPart:
    """Multimodal content element (text, image URL, base64 data)."""

    type: str  # "text", "image_url", "audio"
    text: Optional[str] = None
    image_url: Optional[str] = None
    data: Optional[bytes] = None
    mime_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {"type": self.type}
        if self.text is not None:
            res["text"] = self.text
        if self.image_url is not None:
            res["image_url"] = self.image_url
        if self.mime_type is not None:
            res["mime_type"] = self.mime_type
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContentPart":
        return cls(
            type=data.get("type", "text"),
            text=data.get("text"),
            image_url=data.get("image_url"),
            mime_type=data.get("mime_type"),
        )


@dataclass
class ToolCall:
    """Structured representation of an LLM tool invocation request."""

    id: str
    name: str
    arguments: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCall":
        args = data.get("arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {"raw": args}
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            arguments=args,
        )


@dataclass
class ToolResult:
    """Structured output returned from executing a ToolCall."""

    tool_call_id: str
    content: str
    is_error: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_call_id": self.tool_call_id,
            "content": self.content,
            "is_error": self.is_error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolResult":
        return cls(
            tool_call_id=data.get("tool_call_id", ""),
            content=data.get("content", ""),
            is_error=data.get("is_error", False),
        )


@dataclass
class Message:
    """Provider-neutral conversation message."""

    role: Role
    content: Union[str, List[ContentPart]]
    name: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_text_content(self) -> str:
        if isinstance(self.content, str):
            return self.content
        parts = []
        for part in self.content:
            if part.text:
                parts.append(part.text)
        return " ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        if isinstance(self.content, str):
            c_val: Union[str, List[Dict[str, Any]]] = self.content
        else:
            c_val = [p.to_dict() for p in self.content]

        res: Dict[str, Any] = {
            "role": self.role.value if isinstance(self.role, Role) else str(self.role),
            "content": c_val,
        }
        if self.name is not None:
            res["name"] = self.name
        if self.tool_calls is not None:
            res["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]
        if self.tool_call_id is not None:
            res["tool_call_id"] = self.tool_call_id
        if self.metadata:
            res["metadata"] = self.metadata
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        role_raw = data.get("role", "user")
        role = Role(role_raw) if role_raw in [e.value for e in Role] else Role.USER

        content_raw = data.get("content", "")
        if isinstance(content_raw, list):
            content: Union[str, List[ContentPart]] = [
                ContentPart.from_dict(p) for p in content_raw if isinstance(p, dict)
            ]
        else:
            content = str(content_raw)

        tc_raw = data.get("tool_calls")
        tool_calls = (
            [ToolCall.from_dict(tc) for tc in tc_raw if isinstance(tc, dict)]
            if tc_raw is not None
            else None
        )

        return cls(
            role=role,
            content=content,
            name=data.get("name"),
            tool_calls=tool_calls,
            tool_call_id=data.get("tool_call_id"),
            metadata=data.get("metadata", {}),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        return cls.from_dict(json.loads(json_str))
