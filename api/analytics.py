"""Privacy-safe, best-effort PostHog event capture for the product workflow."""
from __future__ import annotations

import asyncio
import json
import os
import urllib.request
from typing import Any

POSTHOG_HOST = (os.getenv("POSTHOG_HOST") or "https://us.i.posthog.com").rstrip("/")
# This is a PostHog project token (public client identifier), not a secret.
# Deployment configuration can override it without changing application code.
POSTHOG_PROJECT_TOKEN = os.getenv(
    "POSTHOG_PROJECT_TOKEN",
    "phc_znLxdWo55FqfwRkwmzdkeYgTLjFG8y5dwbuxFhJxZP7j",
)


def capture(event: str, distinct_id: str, properties: dict[str, Any] | None = None) -> None:
    """Queue an analytics event without ever blocking or failing the request."""
    if not POSTHOG_PROJECT_TOKEN or not distinct_id:
        return
    payload = {
        "api_key": POSTHOG_PROJECT_TOKEN,
        "event": event,
        "distinct_id": distinct_id,
        "properties": {
            "product": "ai_platform",
            **(properties or {}),
        },
    }
    asyncio.create_task(_send(payload))


async def _send(payload: dict[str, Any]) -> None:
    def request() -> None:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{POSTHOG_HOST}/capture/",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=0.8):
                pass
        except Exception:
            # Analytics must never affect product availability.
            pass

    await asyncio.to_thread(request)
