"""ModelConfig, ResponseFormat, and ToolDefinition Contracts for AI Platform Kernel."""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class ResponseFormatType(str, Enum):
    """Supported response formats."""
    TEXT = "text"
    JSON_OBJECT = "json_object"
    JSON_SCHEMA = "json_schema"


@dataclass
class ResponseFormat:
    """Structured output format configuration."""

    type: ResponseFormatType = ResponseFormatType.TEXT
    json_schema: Optional[Dict[str, Any]] = None
    schema_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "type": self.type.value if isinstance(self.type, ResponseFormatType) else str(self.type)
        }
        if self.json_schema is not None:
            res["json_schema"] = self.json_schema
        if self.schema_name is not None:
            res["schema_name"] = self.schema_name
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResponseFormat":
        fmt_type_raw = data.get("type", "text")
        fmt_type = (
            ResponseFormatType(fmt_type_raw)
            if fmt_type_raw in [e.value for e in ResponseFormatType]
            else ResponseFormatType.TEXT
        )
        return cls(
            type=fmt_type,
            json_schema=data.get("json_schema"),
            schema_name=data.get("schema_name"),
        )


@dataclass
class ToolFunction:
    """JSON Schema definition for a tool function."""

    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema dict

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolFunction":
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            parameters=data.get("parameters", {}),
        )


@dataclass
class ToolDefinition:
    """Tool specification passed to a model provider."""

    type: str = "function"
    function: ToolFunction = field(default_factory=lambda: ToolFunction("", "", {}))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "function": self.function.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolDefinition":
        fn_data = data.get("function", {})
        return cls(
            type=data.get("type", "function"),
            function=ToolFunction.from_dict(fn_data) if isinstance(fn_data, dict) else ToolFunction("", "", {}),
        )


@dataclass
class ModelConfig:
    """Provider-neutral model execution parameters."""

    model_name: str
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    stop_sequences: List[str] = field(default_factory=list)
    response_format: Optional[ResponseFormat] = None
    tools: List[ToolDefinition] = field(default_factory=list)
    tool_choice: Union[str, Dict[str, Any]] = "auto"
    timeout_seconds: float = 60.0
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "stop_sequences": self.stop_sequences,
            "tool_choice": self.tool_choice,
            "timeout_seconds": self.timeout_seconds,
            "extra_params": self.extra_params,
        }
        if self.response_format is not None:
            res["response_format"] = self.response_format.to_dict()
        if self.tools:
            res["tools"] = [t.to_dict() for t in self.tools]
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelConfig":
        rf_data = data.get("response_format")
        rf = ResponseFormat.from_dict(rf_data) if isinstance(rf_data, dict) else None

        tools_data = data.get("tools", [])
        tools = [ToolDefinition.from_dict(t) for t in tools_data if isinstance(t, dict)]

        return cls(
            model_name=data.get("model_name", "unknown"),
            temperature=data.get("temperature", 0.7),
            top_p=data.get("top_p"),
            max_tokens=data.get("max_tokens"),
            stop_sequences=data.get("stop_sequences", []),
            response_format=rf,
            tools=tools,
            tool_choice=data.get("tool_choice", "auto"),
            timeout_seconds=data.get("timeout_seconds", 60.0),
            extra_params=data.get("extra_params", {}),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ModelConfig":
        return cls.from_dict(json.loads(json_str))
