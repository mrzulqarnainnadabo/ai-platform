"""Provider and Model Capability Discovery Metadata for AI Platform Kernel."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class MediaCapability(str, Enum):
    """Supported input/output media modalities."""
    TEXT = "text"
    VISION = "vision"
    AUDIO = "audio"
    VIDEO = "video"


@dataclass
class ModelCapabilities:
    """Describes capabilities of a specific LLM model."""

    supports_streaming: bool = True
    supports_structured_output: bool = True
    supports_tools: bool = True
    supports_vision: bool = False
    supports_audio: bool = False
    max_context_tokens: int = 128000
    max_output_tokens: int = 4096
    supported_media: List[MediaCapability] = field(
        default_factory=lambda: [MediaCapability.TEXT]
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "supports_streaming": self.supports_streaming,
            "supports_structured_output": self.supports_structured_output,
            "supports_tools": self.supports_tools,
            "supports_vision": self.supports_vision,
            "supports_audio": self.supports_audio,
            "max_context_tokens": self.max_context_tokens,
            "max_output_tokens": self.max_output_tokens,
            "supported_media": [m.value for m in self.supported_media],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelCapabilities":
        media_raw = data.get("supported_media", ["text"])
        media = [MediaCapability(m) for m in media_raw if m in [e.value for e in MediaCapability]]
        return cls(
            supports_streaming=data.get("supports_streaming", True),
            supports_structured_output=data.get("supports_structured_output", True),
            supports_tools=data.get("supports_tools", True),
            supports_vision=data.get("supports_vision", False),
            supports_audio=data.get("supports_audio", False),
            max_context_tokens=data.get("max_context_tokens", 128000),
            max_output_tokens=data.get("max_output_tokens", 4096),
            supported_media=media or [MediaCapability.TEXT],
        )


@dataclass
class ProviderCapabilities:
    """Describes capabilities and supported models of a model provider."""

    provider_name: str
    supported_models: List[str] = field(default_factory=list)
    model_capabilities: Dict[str, ModelCapabilities] = field(default_factory=dict)

    def get_model_capabilities(self, model_name: str) -> ModelCapabilities:
        if model_name in self.model_capabilities:
            return self.model_capabilities[model_name]
        return ModelCapabilities()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider_name": self.provider_name,
            "supported_models": self.supported_models,
            "model_capabilities": {
                k: v.to_dict() for k, v in self.model_capabilities.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderCapabilities":
        caps_dict = {}
        for k, v in data.get("model_capabilities", {}).items():
            caps_dict[k] = ModelCapabilities.from_dict(v)
        return cls(
            provider_name=data.get("provider_name", "unknown"),
            supported_models=data.get("supported_models", []),
            model_capabilities=caps_dict,
        )
