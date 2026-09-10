"""Message, Role, ContentPart, ToolCall, and ToolResult Contracts for AI Platform Kernel."""

import base64
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
    """Multimodal content element (text, image URL, audio, binary payload)."""

    type: str  # "text", "image_url", "audio", "binary"
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
        if self.text is not None:
            res["text"] = self.text
        if self.image_url is not None:
            res["image_url"] = self.image_url
        if self.data is not None:
            # Base64 encode binary data for safe JSON round-tripping
            res["data_b64"] = base64.b64encode(self.data).decode("utf-8")
        if self.mime_type is not None:
            res["mime_type"] = self.mime_type
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContentPart":
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        c_type = data.get("type", "text")
        raw_b64 = data.get("data_b64")
        data_bytes = None
        if raw_b64 and isinstance(raw_b64, str):
            data_bytes = base64.b64decode(raw_b64.encode("utf-8"))

        return cls(
            type=str(c_type),
            text=data.get("text"),
            image_url=data.get("image_url"),
            data=data_bytes,
            mime_type=data.get("mime_type"),
        )


@dataclass
class ToolCall:
    """Structured representation of an LLM tool invocation request."""

    id: str
    name: str
    arguments: Dict[str, Any]

    def __post_init__(self) -> None:
        if not self.id or not isinstance(self.id, str):
            raise ValueError("ToolCall id must be a non-empty string")
        if not self.name or not isinstance(self.name, str):
            raise ValueError("ToolCall name must be a non-empty string")
        if not isinstance(self.arguments, dict):
            raise ValueError("ToolCall arguments must be a dictionary")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCall":
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        tc_id = data.get("id", "")
        tc_name = data.get("name", "")
        args = data.get("arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {"raw": args}
        if not tc_id or not tc_name:
            raise ValueError("ToolCall dictionary must contain non-empty 'id' and 'name'")
        return cls(
            id=str(tc_id),
            name=str(tc_name),
            arguments=args if isinstance(args, dict) else {},
        )


@dataclass
class ToolResult:
    """Structured output returned from executing a ToolCall."""

    tool_call_id: str
    content: str
    is_error: bool = False

    def __post_init__(self) -> None:
        if not self.tool_call_id or not isinstance(self.tool_call_id, str):
            raise ValueError("tool_call_id must be a non-empty string")
        if self.content is None:
            raise ValueError("content cannot be None")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_call_id": self.tool_call_id,
            "content": self.content,
            "is_error": self.is_error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolResult":
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        t_id = data.get("tool_call_id", "")
        if not t_id:
            raise ValueError("ToolResult dictionary must contain non-empty 'tool_call_id'")
        return cls(
            tool_call_id=str(t_id),
            content=str(data.get("content", "")),
            is_error=bool(data.get("is_error", False)),
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

    def __post_init__(self) -> None:
        # Convert string role to Role enum if valid, raise ValueError if invalid!
        if isinstance(self.role, str):
            valid_roles = [e.value for e in Role]
            if self.role not in valid_roles:
                raise ValueError(f"Invalid message role '{self.role}'. Must be one of {valid_roles}")
            self.role = Role(self.role)
        elif not isinstance(self.role, Role):
            raise ValueError(f"role must be an instance of Role or valid role string, got {type(self.role)}")

        if self.content is None:
            raise ValueError("Message content cannot be None")

        if isinstance(self.content, list):
            for part in self.content:
                if not isinstance(part, ContentPart):
                    raise ValueError("All elements of content list must be ContentPart instances")

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
            "role": self.role.value,
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
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        role_raw = data.get("role")
        if not role_raw or not isinstance(role_raw, str):
            raise ValueError("Message dictionary must contain a valid 'role'")

        valid_roles = [e.value for e in Role]
        if role_raw not in valid_roles:
            raise ValueError(f"Invalid message role '{role_raw}'. Must be one of {valid_roles}")
        role = Role(role_raw)

        content_raw = data.get("content")
        if content_raw is None:
            raise ValueError("Message dictionary must contain 'content'")

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
            metadata=data.get("metadata", {}) if isinstance(data.get("metadata"), dict) else {},
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        if not isinstance(json_str, str):
            raise ValueError("json_str must be a string")
        return cls.from_dict(json.loads(json_str))
