"""Provider-neutral model configuration contracts."""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from ai_platform.core.messages import ProviderOptions


class ResponseFormatType(str, Enum):
    TEXT = "text"
    JSON_OBJECT = "json_object"
    JSON_SCHEMA = "json_schema"


@dataclass
class ResponseFormat:
    type: ResponseFormatType = ResponseFormatType.TEXT
    json_schema: Optional[Dict[str, Any]] = None
    schema_name: Optional[str] = None

    def __post_init__(self) -> None:
        if isinstance(self.type, str):
            if self.type not in [e.value for e in ResponseFormatType]: raise ValueError(f"Invalid ResponseFormatType '{self.type}'")
            self.type = ResponseFormatType(self.type)
        elif not isinstance(self.type, ResponseFormatType): raise ValueError("type must be ResponseFormatType or valid string")
        if self.json_schema is not None and not isinstance(self.json_schema, dict): raise ValueError("json_schema must be a dictionary")

    def to_dict(self) -> Dict[str, Any]:
        result = {"type": self.type.value}
        if self.json_schema is not None: result["json_schema"] = self.json_schema
        if self.schema_name is not None: result["schema_name"] = self.schema_name
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResponseFormat":
        fmt_type = data.get("type", "text")
        if fmt_type not in [e.value for e in ResponseFormatType]: raise ValueError(f"Invalid ResponseFormatType '{fmt_type}'")
        return cls(type=ResponseFormatType(fmt_type), json_schema=data.get("json_schema"), schema_name=data.get("schema_name"))


@dataclass
class ToolFunction:
    name: str
    description: str
    parameters: Dict[str, Any]

    def __post_init__(self) -> None:
        if not self.name or not isinstance(self.name, str): raise ValueError("ToolFunction name must be a non-empty string")
        if not isinstance(self.parameters, dict): raise ValueError("ToolFunction parameters must be a dictionary")

    def to_dict(self) -> Dict[str, Any]: return {"name": self.name, "description": self.description, "parameters": self.parameters}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolFunction":
        return cls(name=str(data.get("name", "")), description=str(data.get("description", "")), parameters=dict(data.get("parameters", {})))


@dataclass
class ToolDefinition:
    type: str = "function"
    function: ToolFunction = field(default_factory=lambda: ToolFunction("default_tool", "", {}))

    def __post_init__(self) -> None:
        if not self.type or not isinstance(self.type, str): raise ValueError("ToolDefinition type must be a non-empty string")
        if not isinstance(self.function, ToolFunction): raise ValueError("function must be ToolFunction")

    def to_dict(self) -> Dict[str, Any]: return {"type": self.type, "function": self.function.to_dict()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolDefinition":
        fn = data.get("function")
        if not isinstance(fn, dict): raise ValueError("ToolDefinition function must be a dictionary")
        return cls(type=str(data.get("type", "function")), function=ToolFunction.from_dict(fn))


@dataclass
class ModelConfig:
    model_name: str
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    stop_sequences: List[str] = field(default_factory=list)
    response_format: Optional[ResponseFormat] = None
    tools: List[ToolDefinition] = field(default_factory=list)
    tool_choice: Union[str, Dict[str, Any]] = "auto"
    timeout_seconds: float = 60.0
    provider_options: ProviderOptions = field(default_factory=ProviderOptions)

    def __post_init__(self) -> None:
        if not self.model_name or not isinstance(self.model_name, str) or not self.model_name.strip(): raise ValueError("model_name cannot be empty")
        if self.temperature is not None and (not isinstance(self.temperature, (int, float)) or not 0.0 <= self.temperature <= 2.0): raise ValueError("temperature must be between 0.0 and 2.0")
        if self.top_p is not None and (not isinstance(self.top_p, (int, float)) or not 0.0 <= self.top_p <= 1.0): raise ValueError("top_p must be between 0.0 and 1.0")
        if self.max_tokens is not None and (not isinstance(self.max_tokens, int) or self.max_tokens <= 0): raise ValueError("max_tokens must be positive")
        if not isinstance(self.timeout_seconds, (int, float)) or self.timeout_seconds <= 0: raise ValueError("timeout_seconds must be positive")
        if not isinstance(self.provider_options, ProviderOptions): self.provider_options = ProviderOptions.model_validate(self.provider_options)

    @property
    def extra_params(self) -> Dict[str, Any]:
        """Read-only compatibility view for existing provider adapters."""
        return self.provider_options.to_dict()

    def to_dict(self) -> Dict[str, Any]:
        result = {"model_name": self.model_name, "temperature": self.temperature, "top_p": self.top_p,
                  "max_tokens": self.max_tokens, "stop_sequences": self.stop_sequences, "tool_choice": self.tool_choice,
                  "timeout_seconds": self.timeout_seconds, "provider_options": self.provider_options.to_dict()}
        if self.response_format is not None: result["response_format"] = self.response_format.to_dict()
        if self.tools: result["tools"] = [t.to_dict() for t in self.tools]
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelConfig":
        rf = ResponseFormat.from_dict(data["response_format"]) if isinstance(data.get("response_format"), dict) else None
        tools = [ToolDefinition.from_dict(t) for t in data.get("tools", []) if isinstance(t, dict)]
        return cls(model_name=str(data.get("model_name", "")), temperature=data.get("temperature", 0.7), top_p=data.get("top_p"),
                   max_tokens=data.get("max_tokens"), stop_sequences=list(data.get("stop_sequences", [])), response_format=rf,
                   tools=tools, tool_choice=data.get("tool_choice", "auto"), timeout_seconds=float(data.get("timeout_seconds", 60.0)),
                   provider_options=ProviderOptions.model_validate(data.get("provider_options", {})))

    def to_json(self) -> str: return json.dumps(self.to_dict(), indent=2)
    @classmethod
    def from_json(cls, json_str: str) -> "ModelConfig": return cls.from_dict(json.loads(json_str))
