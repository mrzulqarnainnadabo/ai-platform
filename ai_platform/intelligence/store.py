"""Select case store implementation from environment.

INTEL_CASE_STORE=memory → InMemoryCaseRepository (local development/tests)
INTEL_CASE_STORE=supabase → SupabaseCaseRepository using server credentials

On Vercel, the absence of INTEL_CASE_STORE defaults to the durable Supabase
store and therefore fails closed if server credentials are missing.

Server env (never expose to browser):
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY   # preferred for server writes to ai_platform_* tables
  or SUPABASE_SECRET_KEY only if policies explicitly allow (not recommended for this schema)
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from .repository import CaseRepository, InMemoryCaseRepository


class CaseStoreConfigurationError(RuntimeError):
    pass


def _supabase_server_client() -> Any:
    url = (os.getenv("SUPABASE_URL") or "").strip()
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    if not key:
        # Fallback name some hosts use; still server-only.
        key = (os.getenv("SUPABASE_SECRET_KEY") or "").strip()
    if not url or not key:
        raise CaseStoreConfigurationError(
            "INTEL_CASE_STORE=supabase requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY"
        )
    from supabase import create_client

    return create_client(url, key)


@lru_cache(maxsize=1)
def get_case_repository() -> CaseRepository:
    configured = (os.getenv("INTEL_CASE_STORE") or "").strip().lower()
    # Vercel must never silently fall back to process-local storage. Local runs
    # retain the lightweight memory implementation unless explicitly configured.
    mode = configured or ("supabase" if os.getenv("VERCEL") == "1" else "memory")
    if mode in ("memory", "mem", "inmemory"):
        return InMemoryCaseRepository()
    if mode in ("supabase", "postgres", "pg"):
        from .supabase_repository import SupabaseCaseRepository

        return SupabaseCaseRepository(_supabase_server_client())
    raise CaseStoreConfigurationError(f"Unknown INTEL_CASE_STORE={mode!r}")


def reset_case_repository_cache() -> None:
    """Test helper."""
    get_case_repository.cache_clear()
