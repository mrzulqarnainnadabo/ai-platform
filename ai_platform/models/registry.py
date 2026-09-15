"""Server-side model catalog.

The client selects a stable platform model id (for example ``fast-general``).
Provider names, upstream model identifiers, limits and pricing remain server-side.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from string import Template
from typing import Any, Mapping

import yaml

from ai_platform.core.config import ModelConfig
from ai_platform.core.messages import ProviderOptions
from ai_platform.core.errors import InvalidRequestError


@dataclass(frozen=True)
class ModelPolicy:
    id: str
    provider: str
    model: str
    max_tokens: int
    input_cost_per_million: float = 0.0
    output_cost_per_million: float = 0.0
    requests_per_minute: int = 60
    tokens_per_day: int = 100_000

    def build_config(self, **overrides: Any) -> ModelConfig:
        requested_max = overrides.pop("max_tokens", None)
        max_tokens = self.max_tokens if requested_max is None else int(requested_max)
        if max_tokens <= 0 or max_tokens > self.max_tokens:
            raise InvalidRequestError("Requested max_tokens exceeds the server-side model policy")
        return ModelConfig(
            model_name=self.model,
            temperature=overrides.pop("temperature", 0.7),
            top_p=overrides.pop("top_p", None),
            max_tokens=max_tokens,
            stop_sequences=overrides.pop("stop_sequences", []),
            response_format=overrides.pop("response_format", None),
            tools=overrides.pop("tools", []),
            tool_choice=overrides.pop("tool_choice", "auto"),
            timeout_seconds=overrides.pop("timeout_seconds", 60.0),
            provider_options=overrides.pop("provider_options", None) or ProviderOptions(),
        )

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return (
            prompt_tokens * self.input_cost_per_million / 1_000_000
            + completion_tokens * self.output_cost_per_million / 1_000_000
        )


class ModelRegistry:
    """Immutable-at-runtime catalog loaded from YAML."""

    def __init__(self, catalog_path: str | Path | None = None) -> None:
        configured = os.getenv("AI_PLATFORM_MODEL_CATALOG")
        self.catalog_path = Path(catalog_path or configured or Path(__file__).resolve().parents[2] / "config" / "models.yaml")
        self._models = self._load()

    def _load(self) -> dict[str, ModelPolicy]:
        if not self.catalog_path.exists():
            raise RuntimeError(f"Model catalog not found: {self.catalog_path}")
        raw = self.catalog_path.read_text(encoding="utf-8")
        rendered = Template(raw).safe_substitute(os.environ)
        document = yaml.safe_load(rendered) or {}
        entries = document.get("models") if isinstance(document, Mapping) else None
        if not isinstance(entries, Mapping) or not entries:
            raise RuntimeError("Model catalog must contain a non-empty 'models' mapping")
        result: dict[str, ModelPolicy] = {}
        for model_id, value in entries.items():
            if not isinstance(model_id, str) or not isinstance(value, Mapping):
                raise RuntimeError("Invalid model catalog entry")
            provider = str(value.get("provider", "")).strip()
            model = str(value.get("model", "")).strip()
            if not provider or not model:
                raise RuntimeError(f"Model '{model_id}' must define provider and model")
            result[model_id] = ModelPolicy(
                id=model_id,
                provider=provider,
                model=model,
                max_tokens=int(value.get("max_tokens", 4096)),
                input_cost_per_million=float(value.get("input_cost_per_million", 0.0)),
                output_cost_per_million=float(value.get("output_cost_per_million", 0.0)),
                requests_per_minute=int(value.get("requests_per_minute", 60)),
                tokens_per_day=int(value.get("tokens_per_day", 100_000)),
            )
        return result

    def resolve(self, model_id: str) -> ModelPolicy:
        try:
            return self._models[model_id]
        except KeyError as exc:
            raise InvalidRequestError("Unknown model") from exc

    def all(self) -> tuple[ModelPolicy, ...]:
        return tuple(self._models.values())
