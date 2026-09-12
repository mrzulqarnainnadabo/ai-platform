"""Application dependencies for the Vercel/FastAPI host.

Everything here is an application boundary. The provider-neutral platform package
must not import FastAPI, Supabase, or HTTP concerns.

Required environment (server-side only):
  SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY
  OPENAI_API_KEY and/or XAI_API_KEY (for non-loopback providers)

Optional:
  OPENAI_BASE_URL, AI_PLATFORM_PROVIDER, AI_PLATFORM_PROVIDER_TIMEOUT_SECONDS,
  AI_PLATFORM_TENANT_CLAIM, AI_PLATFORM_PERMISSIONS_CLAIM

Do not accept client-supplied tenant_id or permissions — only verified JWT claims.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ai_platform.integrations.supabase_auth import (
    SupabaseAuthContextProvider,
    SupabaseAuthenticationError,
    SupabaseAuthConfigurationError,
)
from ai_platform.policy.authorization import AuthorizationContext
from ai_platform.runtime.authorized import AuthorizedModelRuntime
from ai_platform.runtime.model_runtime import ModelRuntime
from ai_platform.runtime.registry import ProviderRegistry

security = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def get_auth_provider() -> SupabaseAuthContextProvider:
    return SupabaseAuthContextProvider.from_environment()


def require_auth(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> AuthorizationContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        return get_auth_provider().get_context(credentials.credentials)
    except (SupabaseAuthenticationError, SupabaseAuthConfigurationError) as exc:
        # Do not disclose JWT, Supabase SDK, or configuration details to callers.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed") from exc


@lru_cache(maxsize=1)
def get_authorized_runtime() -> AuthorizedModelRuntime:
    registry = ProviderRegistry()
    provider_name = os.getenv("AI_PLATFORM_PROVIDER", "openai-compatible").strip()
    if provider_name == "openai-compatible":
        from ai_platform.providers.openai_compatible import OpenAICompatibleProvider

        base_url = (os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").strip()
        # Prefer provider-specific key when targeting xAI; otherwise OPENAI_API_KEY.
        api_key = (os.getenv("OPENAI_API_KEY") or os.getenv("XAI_API_KEY") or "").strip()
        is_local = base_url.startswith(("http://localhost", "http://127.0.0.1", "http://[::1]"))
        if not api_key and not is_local:
            raise RuntimeError("OPENAI_API_KEY or XAI_API_KEY is required for a non-local provider")

        registry.register(OpenAICompatibleProvider(
            api_key=api_key or None,
            base_url=base_url,
            timeout_seconds=float(os.getenv("AI_PLATFORM_PROVIDER_TIMEOUT_SECONDS", "60")),
        ))
    else:
        raise RuntimeError("No configured provider")
    return AuthorizedModelRuntime(ModelRuntime(registry))


def require_runtime() -> AuthorizedModelRuntime:
    try:
        return get_authorized_runtime()
    except Exception as exc:
        # Provider configuration is intentionally not exposed through the API.
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Model provider is not configured") from exc
