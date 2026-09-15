"""Optional Langfuse v4 sink for safe runtime events.

Set LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY and optionally LANGFUSE_BASE_URL.
Inputs/outputs are intentionally not captured; durable platform rows remain the
source of truth for governance and cost accounting.
"""
from __future__ import annotations

import os
from typing import Any

from ai_platform.observability import RuntimeEvent


class LangfuseEventSink:
    def __init__(self, client: Any | None = None) -> None:
        from langfuse import get_client
        self.client = client or get_client()

    def emit(self, event: RuntimeEvent) -> None:
        try:
            with self.client.start_as_current_observation(
                as_type="span",
                name=event.event_type,
                metadata={"platform_trace_id": event.trace_id, **event.safe_metadata()},
            ):
                pass
        except Exception:
            # Observability must never break model execution.
            return

    def flush(self) -> None:
        try:
            self.client.flush()
        except Exception:
            return


def langfuse_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))
