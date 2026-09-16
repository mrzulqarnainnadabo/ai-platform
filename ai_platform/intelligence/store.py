"""Select durable case store and expose the server-only Supabase client."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from .repository import CaseRepository, InMemoryCaseRepository


class CaseStoreConfigurationError(RuntimeError):
    pass


def _supabase_server_client() -> Any:
    url = (os.getenv("SUPABASE_URL") or "").strip()
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SECRET_KEY") or "").strip()
    if not url or not key:
        raise CaseStoreConfigurationError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    from supabase import create_client
    return create_client(url, key)


@lru_cache(maxsize=1)
def get_supabase_server_client() -> Any:
    return _supabase_server_client()


@lru_cache(maxsize=1)
def get_case_repository() -> CaseRepository:
    configured = (os.getenv("INTEL_CASE_STORE") or "").strip().lower()
    hosted = bool(os.getenv("VERCEL") == "1" or os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID"))
    mode = configured or ("supabase" if hosted else "memory")
    if mode in ("memory", "mem", "inmemory"):
        return InMemoryCaseRepository()
    if mode in ("supabase", "postgres", "pg"):
        from .supabase_repository import SupabaseCaseRepository
        return SupabaseCaseRepository(get_supabase_server_client())
    raise CaseStoreConfigurationError(f"Unknown INTEL_CASE_STORE={mode!r}")


def reset_case_repository_cache() -> None:
    get_case_repository.cache_clear()
    get_supabase_server_client.cache_clear()
