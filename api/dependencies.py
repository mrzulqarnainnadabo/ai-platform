"""Application dependencies for the Vercel/FastAPI host.

Everything here is an application boundary. The provider-neutral platform package
must not import FastAPI, Supabase, or HTTP concerns.
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

        registry.register(OpenAICompatibleProvider(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
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
