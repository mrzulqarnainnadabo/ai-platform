"""HTTP request/response schemas for the protected model endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ai_platform.core.config import ModelConfig
from ai_platform.core.messages import Message


class GenerateRequest(BaseModel):
    """Governed model execution request.

    Requires a valid Supabase Bearer token with platform capability claims.
    Client-supplied tenant or permission fields are ignored; authorization
    comes only from verified JWT claims.
    """

    messages: List[Dict[str, Any]] = Field(
        ...,
        min_length=1,
        description="Conversation messages in role/content form. At least one message is required.",
        examples=[[{"role": "user", "content": "Hello"}]],
    )
    model_name: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Provider model identifier (e.g. gpt-4o-mini, grok-2).",
        examples=["gpt-4o-mini"],
    )
    temperature: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature. Provider may clamp the range.",
    )
    top_p: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter when supported by the provider.",
    )
    max_tokens: Optional[int] = Field(
        default=None,
        gt=0,
        description="Maximum completion tokens when supported by the provider.",
    )
    timeout_seconds: float = Field(
        default=60.0,
        gt=0.0,
        le=300.0,
        description="Per-request execution deadline in seconds (max 300).",
    )
    extra_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional provider-specific parameters passed through the adapter.",
    )
    provider: str = Field(
        default="openai-compatible",
        min_length=1,
        max_length=128,
        description="Registered provider name. Default serves OpenAI and xAI via the OpenAI-compatible adapter.",
        examples=["openai-compatible"],
    )

    def to_platform_inputs(self) -> tuple[List[Message], ModelConfig, str]:
        parsed_messages = [Message.from_dict(item) for item in self.messages]
        config = ModelConfig(
            model_name=self.model_name,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            timeout_seconds=self.timeout_seconds,
            extra_params=self.extra_params,
        )
        return parsed_messages, config, self.provider
