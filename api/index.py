"""Vercel/FastAPI application boundary for the AI platform.

Health endpoints remain public. Model execution requires a verified Supabase
identity and explicit platform capability claims before the provider can run.
"""

from __future__ import annotations

import json
from typing import AsyncGenerator

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse

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

app = FastAPI(title="AI Platform", version=__version__)


def _map_model_exception(exc: Exception) -> HTTPException:
    """Map platform exceptions to public HTTP responses without leaking internals."""
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


@app.get("/api/health/live")
def health_live() -> dict:
    health = liveness(__version__)
    return {"status": health.status.value, "version": health.version, "checks": health.checks}


@app.get("/api/health/ready")
def health_ready() -> dict:
    health = readiness(__version__)
    return {"status": health.status.value, "version": health.version, "checks": health.checks}


@app.get("/api")
def api_root() -> dict:
    return {
        "name": "AI Platform",
        "version": __version__,
        "status": "foundation",
        "model_execution": "protected-application-boundary-required",
        "endpoints": {
            "generate": "POST /api/v1/models/generate",
            "stream": "POST /api/v1/models/stream",
        },
    }


@app.post("/api/v1/models/generate")
async def generate(
    request: GenerateRequest,
    auth: AuthorizationContext = Depends(require_auth),
    runtime: AuthorizedModelRuntime = Depends(require_runtime),
) -> dict:
    """Execute one governed model request for an authenticated caller."""
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


@app.post("/api/v1/models/stream")
async def stream(
    request: GenerateRequest,
    auth: AuthorizationContext = Depends(require_auth),
    runtime: AuthorizedModelRuntime = Depends(require_runtime),
) -> StreamingResponse:
    """Stream a governed model response as native SSE for an authenticated caller.

    Authorization, capability check, and tenant validation occur before any
    provider bytes are produced. Denied requests never reach the provider and
    return HTTP 403 (not a streamed error event).
    """
    try:
        messages, config, provider = request.to_platform_inputs()
        # Eagerly materialize the async generator so _authorize / tenant checks
        # run before we return StreamingResponse. This preserves fail-closed
        # HTTP status semantics for DENY / REQUIRE_HUMAN.
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
