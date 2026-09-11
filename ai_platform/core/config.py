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

    def __post_init__(self) -> None:
        if isinstance(self.type, str):
            valid_types = [e.value for e in ResponseFormatType]
            if self.type not in valid_types:
                raise ValueError(f"Invalid ResponseFormatType '{self.type}'. Must be one of {valid_types}")
            self.type = ResponseFormatType(self.type)
        elif not isinstance(self.type, ResponseFormatType):
            raise ValueError(f"type must be ResponseFormatType or valid string, got {type(self.type)}")

        if self.json_schema is not None and not isinstance(self.json_schema, dict):
            raise ValueError("json_schema must be a dictionary if provided")

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "type": self.type.value
        }
        if self.json_schema is not None:
            res["json_schema"] = self.json_schema
        if self.schema_name is not None:
            res["schema_name"] = self.schema_name
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResponseFormat":
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        fmt_type_raw = data.get("type", "text")
        valid_types = [e.value for e in ResponseFormatType]
        if fmt_type_raw not in valid_types:
            raise ValueError(f"Invalid ResponseFormatType '{fmt_type_raw}'. Must be one of {valid_types}")
        fmt_type = ResponseFormatType(fmt_type_raw)

        schema = data.get("json_schema")
        if schema is not None and not isinstance(schema, dict):
            raise ValueError("json_schema in ResponseFormat dictionary must be a dictionary")

        return cls(
            type=fmt_type,
            json_schema=schema,
            schema_name=data.get("schema_name"),
        )


@dataclass
class ToolFunction:
    """JSON Schema definition for a tool function."""

    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema dict

    def __post_init__(self) -> None:
        if not self.name or not isinstance(self.name, str):
            raise ValueError("ToolFunction name must be a non-empty string")
        if not isinstance(self.parameters, dict):
            raise ValueError("ToolFunction parameters must be a dictionary")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolFunction":
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        name = data.get("name")
        params = data.get("parameters", {})
        if not name or not isinstance(name, str):
            raise ValueError("ToolFunction dictionary must contain a non-empty string 'name'")
        if not isinstance(params, dict):
            raise ValueError("ToolFunction 'parameters' must be a dictionary")
        return cls(
            name=name,
            description=str(data.get("description", "")),
            parameters=params,
        )


@dataclass
class ToolDefinition:
    """Tool specification passed to a model provider."""

    type: str = "function"
    function: ToolFunction = field(default_factory=lambda: ToolFunction("default_tool", "", {}))

    def __post_init__(self) -> None:
        if not self.type or not isinstance(self.type, str):
            raise ValueError("ToolDefinition type must be a non-empty string")
        if not isinstance(self.function, ToolFunction):
            raise ValueError("function must be an instance of ToolFunction")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "function": self.function.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolDefinition":
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        fn_data = data.get("function")
        if not isinstance(fn_data, dict):
            raise ValueError("ToolDefinition dictionary must contain 'function' dict")
        return cls(
            type=str(data.get("type", "function")),
            function=ToolFunction.from_dict(fn_data),
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

    def __post_init__(self) -> None:
        if not self.model_name or not isinstance(self.model_name, str) or not self.model_name.strip():
            raise ValueError("model_name cannot be empty")

        if self.temperature is not None:
            if not isinstance(self.temperature, (int, float)) or not (0.0 <= self.temperature <= 2.0):
                raise ValueError(f"temperature must be between 0.0 and 2.0, got {self.temperature}")

        if self.top_p is not None:
            if not isinstance(self.top_p, (int, float)) or not (0.0 <= self.top_p <= 1.0):
                raise ValueError(f"top_p must be between 0.0 and 1.0, got {self.top_p}")

        if self.max_tokens is not None:
            if not isinstance(self.max_tokens, int) or self.max_tokens <= 0:
                raise ValueError(f"max_tokens must be a positive integer, got {self.max_tokens}")

        if not isinstance(self.timeout_seconds, (int, float)) or self.timeout_seconds <= 0.0:
            raise ValueError(f"timeout_seconds must be a positive number, got {self.timeout_seconds}")

        if not isinstance(self.stop_sequences, list):
            raise ValueError("stop_sequences must be a list")

        if not isinstance(self.tools, list):
            raise ValueError("tools must be a list")

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
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        m_name = data.get("model_name")
        if not m_name or not isinstance(m_name, str) or not m_name.strip():
            raise ValueError("model_name cannot be empty")

        rf_data = data.get("response_format")
        rf = ResponseFormat.from_dict(rf_data) if isinstance(rf_data, dict) else None

        tools_data = data.get("tools", [])
        if not isinstance(tools_data, list):
            raise ValueError("tools in ModelConfig dictionary must be a list")
        tools = [ToolDefinition.from_dict(t) for t in tools_data if isinstance(t, dict)]

        return cls(
            model_name=m_name,
            temperature=data.get("temperature", 0.7),
            top_p=data.get("top_p"),
            max_tokens=data.get("max_tokens"),
            stop_sequences=list(data.get("stop_sequences", [])),
            response_format=rf,
            tools=tools,
            tool_choice=data.get("tool_choice", "auto"),
            timeout_seconds=float(data.get("timeout_seconds", 60.0)),
            extra_params=dict(data.get("extra_params", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ModelConfig":
        if not isinstance(json_str, str):
            raise ValueError("json_str must be a string")
        return cls.from_dict(json.loads(json_str))
