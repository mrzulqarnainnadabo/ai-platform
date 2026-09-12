"""Vercel entrypoint: preserve the existing host and register intelligence routes."""
from __future__ import annotations

import uuid

from fastapi import Request, Response

from api.analytics import capture
from api.original_index import app, handler
from api.intelligence import router as intelligence_router
from api.cases_frontend import cases_page

app.include_router(intelligence_router)


@app.middleware("http")
async def product_analytics(request: Request, call_next):
    """Capture safe workflow milestones without collecting case or evidence content."""
    distinct_id = request.cookies.get("ai_platform_analytics_id") or str(uuid.uuid4())
    path = request.url.path
    method = request.method
    event: str | None = None
    properties: dict[str, object] = {"http_method": method}

    if path == "/app/cases" and method == "GET":
        event = "case_workspace_viewed"
    elif path == "/api/v1/cases" and method == "GET":
        event = "case_workspace_viewed"
    elif path == "/api/v1/cases" and method == "POST":
        event = "case_created"
    elif path.startswith("/api/v1/cases/") and path.endswith("/triage") and method == "POST":
        event = "case_triage_started"
    elif path.startswith("/api/v1/cases/") and path.endswith("/evidence") and method == "POST":
        event = "evidence_added"
    elif path.startswith("/api/v1/cases/") and method == "GET":
        event = "case_opened"

    try:
        response = await call_next(request)
    except Exception:
        capture("api_error", distinct_id, {**properties, "error_class": "unhandled_exception"})
        raise

    if event:
        if event == "case_triage_started":
            capture(event, distinct_id, properties)
            capture(
                "case_triage_completed",
                distinct_id,
                {**properties, "success": 200 <= response.status_code < 300},
            )
        elif event == "case_created":
            capture(event, distinct_id, {**properties, "success": 200 <= response.status_code < 300})
        elif event == "evidence_added":
            capture(event, distinct_id, {**properties, "success": 200 <= response.status_code < 300})
        else:
            capture(event, distinct_id, properties)

    if response.status_code == 403:
        capture("authorization_denied", distinct_id, {**properties, "status_code": 403})
    elif response.status_code >= 500:
        capture("api_error", distinct_id, {**properties, "status_code": response.status_code})

    response.set_cookie(
        "ai_platform_analytics_id",
        distinct_id,
        max_age=60 * 60 * 24 * 365,
        httponly=True,
        secure=True,
        samesite="lax",
    )
    return response


# The case workspace is a browser shell only; authentication and authorization
# happen through Supabase Auth + the protected /api/v1/cases API.


@app.get("/app/cases", include_in_schema=False)
def intelligence_cases_app() -> Response:
    return cases_page()


# Extend the existing OpenAPI security decoration to the new authenticated case routes.
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
