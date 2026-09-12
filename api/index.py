"""Vercel/FastAPI application boundary for the AI platform.

Public discovery and health endpoints remain unauthenticated.
Model execution requires a verified Supabase identity and explicit platform
capability claims before any provider is contacted.
"""

from __future__ import annotations

import sys
from pathlib import Path as _Path

# Ensure repository root is on sys.path when Vercel invokes api/index.py.
_HERE = _Path(__file__).resolve().parent
_ROOT = _HERE.parent
for _candidate in (_ROOT, _HERE, _Path.cwd(), _Path.cwd().parent):
    _s = str(_candidate)
    if _s not in sys.path:
        sys.path.insert(0, _s)

import json
from typing import AsyncGenerator

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse

from ai_platform import __version__
from ai_platform.core.errors import (
    AuthenticationError,
    CancellationError,
    InvalidRequestError,
    ProviderQuotaError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitError,
)
from ai_platform.health import liveness, readiness
from ai_platform.policy.authorization import AuthorizationContext
from ai_platform.policy.errors import HumanApprovalRequiredError, PolicyDeniedError
from ai_platform.runtime.authorized import AuthorizedModelRuntime
from api.dependencies import require_auth, require_runtime
from api.models import GenerateRequest

app = FastAPI(
    title="AI Platform",
    version=__version__,
    description=(
        "Provider-neutral, governed AI execution infrastructure. "
        "OpenAI and xAI/Grok share the same OpenAI-compatible adapter and the same "
        "deterministic authorization path. Model endpoints require a verified Supabase "
        "JWT with platform capability claims. AI output is never institutional authority."
    ),
    contact={"name": "AI Platform", "url": "https://github.com/mrzulqarnainnadabo/ai-platform"},
    license_info={"name": "Apache-2.0 (upstream foundation retained)"},
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "discovery", "description": "Public product and health discovery"},
        {"name": "models", "description": "Governed model execution (authenticated)"},
    ],
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
        contact=app.contact,
        license_info=app.license_info,
    )
    schema["components"] = schema.get("components") or {}
    schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Supabase access token. Must include ai_platform_tenant_id and ai_platform_permissions claims from the custom access-token hook.",
        }
    }
    for path_item in schema.get("paths", {}).values():
        for method, op in path_item.items():
            if method in ("post", "put", "patch", "delete") and isinstance(op, dict):
                if op.get("tags") and "models" in op["tags"]:
                    op["security"] = [{"HTTPBearer": []}]
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore[method-assign]


def _map_model_exception(exc: Exception) -> HTTPException:
    if isinstance(exc, PolicyDeniedError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Model capability denied")
    if isinstance(exc, HumanApprovalRequiredError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Human approval required")
    if isinstance(exc, (InvalidRequestError, ValueError)):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid model request")
    if isinstance(exc, AuthenticationError):
        return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Model provider authentication failed")
    if isinstance(exc, RateLimitError):
        return HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Model provider rate limit reached")
    if isinstance(exc, ProviderQuotaError):
        return HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Model provider quota unavailable")
    if isinstance(exc, ProviderTimeoutError):
        return HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Model provider timed out")
    if isinstance(exc, CancellationError):
        return HTTPException(status_code=status.HTTP_499_CLIENT_CLOSED_REQUEST, detail="Model request cancelled")
    if isinstance(exc, ProviderUnavailableError):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model provider unavailable")
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Model provider request failed")


@app.get("/", response_class=HTMLResponse, include_in_schema=False, tags=["discovery"])
def public_landing() -> str:
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\"/>
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"/>
  <title>AI Platform \u2014 Governed, provider-neutral AI execution</title>
  <meta name=\"description\" content=\"Secure, provider-neutral AI execution infrastructure. OpenAI and xAI/Grok share one governed authorization path. Deterministic policy. Fail-closed security.\"/>
  <meta name=\"robots\" content=\"index,follow\"/>
  <link rel=\"canonical\" href=\"/\"/>
  <meta property=\"og:title\" content=\"AI Platform \u2014 Governed AI execution\"/>
  <meta property=\"og:description\" content=\"Provider-neutral infrastructure for authenticated model generation and streaming. OpenAI + xAI/Grok. Deterministic authorization.\"/>
  <meta property=\"og:type\" content=\"website\"/>
  <meta property=\"og:site_name\" content=\"AI Platform\"/>
  <meta name=\"twitter:card\" content=\"summary\"/>
  <meta name=\"twitter:title\" content=\"AI Platform \u2014 Governed AI execution\"/>
  <meta name=\"twitter:description\" content=\"Provider-neutral, authenticated model execution. OpenAI and xAI/Grok. Fail-closed policy.\"/>
  <style>
    :root {{ color-scheme: light dark; --fg: #1a1a1a; --muted: #555; --bg: #fafafa; --card: #fff; --border: #e5e5e5; --accent: #0b5fff; }}
    @media (prefers-color-scheme: dark) {{
      :root {{ --fg: #f0f0f0; --muted: #aaa; --bg: #0f0f0f; --card: #1a1a1a; --border: #333; --accent: #6b9fff; }}
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; background: var(--bg); color: var(--fg); line-height: 1.55; }}
    main {{ max-width: 40rem; margin: 0 auto; padding: 2rem 1.25rem 4rem; }}
    h1 {{ font-size: 1.75rem; margin: 0 0 0.5rem; letter-spacing: -0.02em; }}
    .lead {{ color: var(--muted); font-size: 1.05rem; margin-bottom: 1.5rem; }}
    .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1rem 1.15rem; margin: 1rem 0; }}
    ul {{ padding-left: 1.2rem; margin: 0.5rem 0; }}
    a {{ color: var(--accent); }}
    .meta {{ font-size: 0.9rem; color: var(--muted); margin-top: 2rem; }}
  </style>
</head>
<body>
  <main>
    <h1>AI Platform</h1>
    <p class=\"lead\">Secure, provider-neutral infrastructure for governed AI model execution.</p>
    <div class=\"card\">
      <strong>What it is</strong>
      <ul>
        <li>Authenticated model generation and streaming</li>
        <li>OpenAI and xAI/Grok via one OpenAI-compatible adapter</li>
        <li>Deterministic authorization \u2014 AI is never institutional authority</li>
        <li>Fail-closed policy, tenant isolation, server-side credentials only</li>
      </ul>
    </div>
    <div class=\"card\">
      <strong>For developers</strong>
      <ul>
        <li><a href=\"/docs\">Interactive API docs (OpenAPI)</a></li>
        <li><a href=\"/redoc\">ReDoc</a></li>
        <li><a href=\"/api\">Machine-readable discovery</a></li>
        <li><a href=\"https://github.com/mrzulqarnainnadabo/ai-platform\">Source on GitHub</a></li>
      </ul>
    </div>
    <div class=\"card\">
      <strong>Status</strong>
      <p style=\"margin:0.4rem 0 0\">Version {__version__}. Health: <a href=\"/api/health/live\">liveness</a> \u00b7 <a href=\"/api/health/ready\">readiness</a>. Model endpoints require a Supabase Bearer token with platform capabilities.</p>
    </div>
    <p class=\"meta\">No provider API keys in the browser. No client-manufactured permissions. Apache-2.0 upstream foundation retained with attribution.</p>
  </main>
</body>
</html>
"""


@app.get("/robots.txt", response_class=PlainTextResponse, include_in_schema=False, tags=["discovery"])
def robots_txt() -> str:
    return """User-agent: *
Allow: /
Allow: /docs
Allow: /redoc
Allow: /api
Allow: /api/health/
Disallow: /api/v1/
Sitemap: /sitemap.xml
"""


@app.get("/sitemap.xml", response_class=PlainTextResponse, include_in_schema=False, tags=["discovery"])
def sitemap_xml() -> str:
    return """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">
  <url><loc>/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>
  <url><loc>/docs</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>
  <url><loc>/redoc</loc><changefreq>weekly</changefreq><priority>0.6</priority></url>
  <url><loc>/api</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>
  <url><loc>/api/health/live</loc><changefreq>daily</changefreq><priority>0.3</priority></url>
</urlset>
"""


@app.get("/api/health/live", tags=["discovery"])
def health_live() -> dict:
    health = liveness(__version__)
    return {"status": health.status.value, "version": health.version, "checks": health.checks}


@app.get("/api/health/ready", tags=["discovery"])
def health_ready() -> dict:
    health = readiness(__version__)
    return {"status": health.status.value, "version": health.version, "checks": health.checks}


@app.get("/api", tags=["discovery"])
def api_root() -> dict:
    return {
        "name": "AI Platform",
        "version": __version__,
        "status": "foundation",
        "description": "Provider-neutral governed AI execution. OpenAI and xAI/Grok share one authorization path.",
        "model_execution": "protected-application-boundary-required",
        "authentication": "Supabase Bearer JWT with ai_platform_tenant_id and ai_platform_permissions claims",
        "endpoints": {
            "generate": "POST /api/v1/models/generate",
            "stream": "POST /api/v1/models/stream",
            "docs": "GET /docs",
            "health_live": "GET /api/health/live",
            "health_ready": "GET /api/health/ready",
        },
        "providers": ["openai-compatible"],
        "notes": [
            "AI output is never institutional authority.",
            "Client-supplied tenant or permission fields are ignored.",
            "Denied requests never reach the model provider.",
        ],
    }


@app.post("/api/v1/models/generate", tags=["models"])
async def generate(
    request: GenerateRequest,
    auth: AuthorizationContext = Depends(require_auth),
    runtime: AuthorizedModelRuntime = Depends(require_runtime),
) -> dict:
    try:
        messages, config, provider = request.to_platform_inputs()
        result = await runtime.generate(auth, messages, config, provider)
    except Exception as exc:
        raise _map_model_exception(exc) from exc
    return {
        "id": result.response.response_id,
        "provider": result.response.provider_name,
        "model": result.response.model_name,
        "finish_reason": result.response.finish_reason.value,
        "message": result.response.message.to_dict(),
        "usage": result.response.usage.to_dict(),
        "trace_id": result.metadata.get("trace_id"),
    }


@app.post("/api/v1/models/stream", tags=["models"])
async def stream(
    request: GenerateRequest,
    auth: AuthorizationContext = Depends(require_auth),
    runtime: AuthorizedModelRuntime = Depends(require_runtime),
) -> StreamingResponse:
    try:
        messages, config, provider = request.to_platform_inputs()
        stream_gen = runtime.stream(auth, messages, config, provider)
        aiter = stream_gen.__aiter__()
        first = await aiter.__anext__()
    except StopAsyncIteration:
        async def empty_gen() -> AsyncGenerator[str, None]:
            yield "data: [DONE]\n\n"
        return StreamingResponse(empty_gen(), media_type="text/event-stream")
    except Exception as exc:
        raise _map_model_exception(exc) from exc

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            payload = {
                "id": first.response.response_id,
                "provider": first.response.provider_name,
                "model": first.response.model_name,
                "finish_reason": first.response.finish_reason.value,
                "message": first.response.message.to_dict(),
                "usage": first.response.usage.to_dict(),
                "trace_id": first.metadata.get("trace_id"),
            }
            yield f"data: {json.dumps(payload)}\n\n"
            async for result in aiter:
                payload = {
                    "id": result.response.response_id,
                    "provider": result.response.provider_name,
                    "model": result.response.model_name,
                    "finish_reason": result.response.finish_reason.value,
                    "message": result.response.message.to_dict(),
                    "usage": result.response.usage.to_dict(),
                    "trace_id": result.metadata.get("trace_id"),
                }
                yield f"data: {json.dumps(payload)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:
            mapped = _map_model_exception(exc)
            yield f"data: {json.dumps({'error': mapped.detail, 'status': mapped.status_code})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# AWS/Vercel-compatible ASGI adapter (used when runtime expects `handler`).
try:
    from mangum import Mangum

    handler = Mangum(app)
except Exception:  # pragma: no cover - optional at runtime
    handler = app  # type: ignore[assignment]
