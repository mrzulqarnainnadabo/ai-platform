from enum import Enum


class Capability(str, Enum):
    MODEL_GENERATE = "model.generate"
    MODEL_STREAM = "model.stream"


def parse_capability(value: str) -> Capability:
    try:
        return Capability(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Unknown capability: {value!r}") from exc
