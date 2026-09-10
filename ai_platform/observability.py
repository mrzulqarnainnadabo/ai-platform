"""Provider-neutral, secret-safe runtime events."""
from dataclasses import dataclass, field
from typing import Any, Dict, Protocol

_SENSITIVE = {"prompt", "prompts", "response", "responses", "content", "api_key", "authorization", "token", "secret"}


def sanitize(metadata: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in metadata.items() if k.lower() not in _SENSITIVE}


@dataclass(frozen=True)
class RuntimeEvent:
    event_type: str
    trace_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def safe_metadata(self) -> Dict[str, Any]:
        return sanitize(self.metadata)


class EventSink(Protocol):
    def emit(self, event: RuntimeEvent) -> None: ...


class InMemoryEventSink:
    def __init__(self) -> None:
        self.events = []

    def emit(self, event: RuntimeEvent) -> None:
        self.events.append(RuntimeEvent(event.event_type, event.trace_id, sanitize(event.metadata)))
