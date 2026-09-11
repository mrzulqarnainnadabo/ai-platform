"""Authorization capabilities (what a principal may invoke).

Distinct from ``ai_platform.core.capabilities``, which describes model/provider
*media and feature* metadata (streaming support, vision, tools, etc.).

This module is only about fail-closed permission strings such as
``model.generate`` and ``model.stream``.
"""
from enum import Enum


class Capability(str, Enum):
    MODEL_GENERATE = "model.generate"
    MODEL_STREAM = "model.stream"


def parse_capability(value: str) -> Capability:
    try:
        return Capability(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Unknown capability: {value!r}") from exc
