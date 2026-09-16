"""FastAPI entrypoint: preserve the existing host and register intelligence routes."""
from __future__ import annotations

import uuid
from http.cookies import SimpleCookie
from typing import Any

from fastapi import Response
from starlette.datastructures import MutableHeaders

from api.analytics import capture
from api.original_index import app, handler
from api.intelligence import router as intelligence_router
from api.cases_auth_frontend import cases_auth_page
from api.frontdoor import app_frontdoor

app.include_router(intelligence_router)


class ProductAnalyticsMiddleware:
    """Secret-safe analytics middleware implemented as pure ASGI."""

    def __init__(self, app: Any) -> None:
        self.app = app

    @staticmethod
    def _analytics_id(headers: list[tuple[bytes, bytes]]) -> str:
        cookie_header = next((value for key, value in headers if key.lower() == b"cookie"), b"")
        cookies = SimpleCookie()
        try:
            cookies.load(cookie_header.decode("latin-1"))
            existing = cookies.get("ai_platform_analytics_id")
            if existing and existing.value:
                return existing.value
        except Exception:
            pass
        return str(uuid.uuid4())

    @staticmethod
    def _event_for(path: str, method: str) -> str | None:
        if path == "/app/cases" and method == "GET":
            return "case_workspace_viewed"
        if path == "/api/v1/cases" and method == "GET":
            return "case_workspace_viewed"
        if path == "/api/v1/cases" and method == "POST":
            return "case_created"
        if path.startswith("/api/v1/cases/") and path.endswith("/triage") and method == "POST":
            return "case_triage_started"
        if path.startswith("/api/v1/cases/") and path.endswith("/evidence") and method == "POST":
            return "evidence_added"
        if path.startswith("/api/v1/cases/") and method == "GET":
            return "case_opened"
        return None

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        path = scope.get("path", "")
        method = scope.get("method", "GET")
        headers = scope.get("headers", [])
        distinct_id = self._analytics_id(headers)
        event = self._event_for(path, method)
        properties: dict[str, object] = {"http_method": method}
        response_status: int | None = None

        async def send_wrapper(message: dict) -> None:
            nonlocal response_status
            if message.get("type") == "http.response.start":
                response_status = int(message.get("status", 500))
                MutableHeaders(scope=message).append(
                    "set-cookie",
                    f"ai_platform_analytics_id={distinct_id}; Max-Age={60 * 60 * 24 * 365}; Path=/; HttpOnly; Secure; SameSite=Lax",
                )
                if event:
                    if event == "case_triage_started":
                        capture(event, distinct_id, properties)
                        capture("case_triage_completed", distinct_id, {**properties, "success": 200 <= response_status < 300})
                    elif event in {"case_created", "evidence_added"}:
                        capture(event, distinct_id, {**properties, "success": 200 <= response_status < 300})
                    else:
                        capture(event, distinct_id, properties)
                if response_status == 403:
                    capture("authorization_denied", distinct_id, {**properties, "status_code": 403})
                elif response_status >= 500:
                    capture("api_error", distinct_id, {**properties, "status_code": response_status})
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            capture("api_error", distinct_id, {**properties, "error_class": "unhandled_exception"})
            raise


app.add_middleware(ProductAnalyticsMiddleware)


@app.get("/app", include_in_schema=False)
def intelligence_app_frontdoor() -> str:
    return app_frontdoor()


@app.get("/app/cases", include_in_schema=False)
def intelligence_cases_app() -> Response:
    return cases_auth_page()


_base_openapi = app.openapi


def intelligence_openapi():
    schema = _base_openapi()
    for path, operations in schema.get("paths", {}).items():
        if path.startswith("/api/v1/cases"):
            for operation in operations.values():
                if isinstance(operation, dict):
                    operation["security"] = [{"HTTPBearer": []}]
    return schema


app.openapi = intelligence_openapi  # type: ignore[method-assign]
