"""HTTP schemas for governed model execution."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from ai_platform.core.config import ModelConfig
from ai_platform.core.messages import Message, ProviderOptions
from ai_platform.models.registry import ModelPolicy, ModelRegistry


class GenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    messages: List[Dict[str, Any]] = Field(..., min_length=1)
    model_name: str = Field(default="fast-general", min_length=1, max_length=128)
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    timeout_seconds: float = Field(default=60.0, gt=0.0, le=300.0)
    provider_options: ProviderOptions = Field(default_factory=ProviderOptions)

    def to_platform_inputs(self, registry: ModelRegistry | None = None) -> tuple[List[Message], ModelConfig, str]:
        policy: ModelPolicy = (registry or ModelRegistry()).resolve(self.model_name)
        parsed_messages = [Message.from_dict(item) for item in self.messages]
        config = policy.build_config(temperature=self.temperature, top_p=self.top_p, max_tokens=self.max_tokens,
                                     timeout_seconds=self.timeout_seconds, provider_options=self.provider_options)
        # Keep the existing API tuple contract while carrying the resolved policy
        # internally. The client never supplies provider or upstream model names.
        setattr(config, "_model_policy", policy)
        return parsed_messages, config, policy.provider
