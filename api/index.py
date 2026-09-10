"""Vercel/FastAPI application boundary for the AI platform.

Health endpoints remain public. Model execution requires a verified Supabase
identity and explicit platform capability claims before the provider can run.
"""

from fastapi import Depends, FastAPI, HTTPException, status

from ai_platform import __version__
from ai_platform.health import liveness, readiness
from ai_platform.policy.authorization import AuthorizationContext
from ai_platform.runtime.authorized import AuthorizedModelRuntime
from api.dependencies import require_auth, require_runtime
from api.models import GenerateRequest

app = FastAPI(title="AI Platform", version=__version__)


@app.get("/api/health/live")
def health_live() -> dict:
    health = liveness(__version__)
    return {
        "status": health.status.value,
        "version": health.version,
        "checks": health.checks,
    }


@app.get("/api/health/ready")
def health_ready() -> dict:
    health = readiness(__version__)
    return {
        "status": health.status.value,
        "version": health.version,
        "checks": health.checks,
    }


@app.get("/api")
def api_root() -> dict:
    return {
        "name": "AI Platform",
        "version": __version__,
        "status": "protected-foundation",
        "model_execution": "authenticated-and-capability-gated",
    }


@app.post("/api/v1/models/generate")
async def generate(
    request: GenerateRequest,
    auth: AuthorizationContext = Depends(require_auth),
    runtime: AuthorizedModelRuntime = Depends(require_runtime),
) -> dict:
    """Execute one governed model request for an authenticated caller.

    Authorization is performed before the provider is resolved/executed. The
    endpoint never accepts a role, permission, tenant, or approval value from
    the request body; those values come from the verified identity boundary.
    """
    try:
        messages, config, provider = request.to_platform_inputs()
        result = await runtime.generate(auth, messages, config, provider)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid model request") from exc
    except Exception as exc:
        # The platform runtime/provider layers sanitize their own errors. Keep
        # application responses generic so provider credentials/details never leak.
        from ai_platform.policy.errors import HumanApprovalRequiredError, PolicyDeniedError

        if isinstance(exc, PolicyDeniedError):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Model capability denied") from exc
        if isinstance(exc, HumanApprovalRequiredError):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Human approval required") from exc
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Model provider request failed") from exc

    return {
        "id": result.response.response_id,
        "provider": result.response.provider_name,
        "model": result.response.model_name,
        "finish_reason": result.response.finish_reason.value,
        "message": result.response.message.to_dict(),
        "usage": result.response.usage.to_dict(),
        "trace_id": result.trace_id,
    }
