"""Small Vercel deployment host for the provider-neutral AI platform.

This host intentionally exposes health/readiness only until a real application
AuthN/AuthZ boundary is wired. Model execution must not be exposed anonymously.
"""
from fastapi import FastAPI

from ai_platform import __version__
from ai_platform.health import liveness, readiness

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
        "status": "foundation",
        "model_execution": "protected-application-boundary-required",
    }
