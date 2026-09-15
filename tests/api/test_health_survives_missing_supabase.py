"""Regression: /api/health/live must not depend on Supabase at import time.

On Vercel, INTEL_CASE_STORE defaults to supabase when VERCEL=1. Prior to the
lazy-init fix, importing api.intelligence constructed the case repository at
module load, which raised CaseStoreConfigurationError when SUPABASE_URL /
SUPABASE_SERVICE_ROLE_KEY were absent and made the entire serverless function
return FUNCTION_INVOCATION_FAILED — including the liveness endpoint.
"""
from __future__ import annotations

import importlib
import os
import sys

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def vercel_without_supabase(monkeypatch):
    # Simulate the production Vercel process environment without secrets.
    monkeypatch.setenv("VERCEL", "1")
    for key in (
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_SECRET_KEY",
        "INTEL_CASE_STORE",
    ):
        monkeypatch.delenv(key, raising=False)

    # Force a clean re-import of the application boundary modules so module-level
    # initialization (if any) is exercised under this environment.
    for mod in list(sys.modules):
        if mod == "api" or mod.startswith("api.") or mod.startswith("ai_platform.intelligence"):
            del sys.modules[mod]

    yield


def test_app_import_and_liveness_without_supabase(vercel_without_supabase):
    index = importlib.import_module("api.index")
    client = TestClient(index.app)
    response = client.get("/api/health/live")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["checks"]["process"] == "up"


def test_case_store_failure_is_deferred_to_case_routes(vercel_without_supabase):
    """Case routes may fail closed on missing store; health must not."""
    from ai_platform.intelligence.store import CaseStoreConfigurationError, get_case_repository, reset_case_repository_cache

    reset_case_repository_cache()
    with pytest.raises(CaseStoreConfigurationError):
        get_case_repository()
    reset_case_repository_cache()
