"""FastAPI dependencies for authentication, model policy and durable runtime."""
from __future__ import annotations
import os
from functools import lru_cache
from typing import Annotated
from urllib.parse import urlparse
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from ai_platform.integrations.supabase_auth import SupabaseAuthContextProvider, SupabaseAuthenticationError, SupabaseAuthConfigurationError
from ai_platform.intelligence.store import get_supabase_server_client
from ai_platform.models.registry import ModelRegistry
from ai_platform.policy.approval import ApprovalService
from ai_platform.policy.authorization import AuthorizationContext
from ai_platform.policy.rate_limits import RateLimitPolicy, SupabaseRateLimitStore
from ai_platform.runtime.authorized import AuthorizedModelRuntime
from ai_platform.runtime.model_runtime import ModelRuntime
from ai_platform.runtime.registry import ProviderRegistry
from ai_platform.runtime.run_engine import RunEngine, SupabaseRunStore

security = HTTPBearer(auto_error=False)


def _is_loopback_base_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and parsed.hostname in {"localhost", "127.0.0.1", "::1"}


def _resolve_cloud_provider_credentials() -> tuple[str, str]:
    base_url = (os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").strip()
    if base_url.rstrip("/").lower() == "https://api.x.ai/v1":
        key = (os.getenv("XAI_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    else:
        key = (os.getenv("OPENAI_API_KEY") or os.getenv("XAI_API_KEY") or "").strip()
    return base_url, key


def default_model_name() -> str:
    return (os.getenv("AI_PLATFORM_DEFAULT_MODEL") or "fast-general").strip()


@lru_cache(maxsize=1)
def get_auth_provider() -> SupabaseAuthContextProvider:
    return SupabaseAuthContextProvider.from_environment()


@lru_cache(maxsize=1)
def get_model_registry() -> ModelRegistry:
    return ModelRegistry()


def require_auth(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)]) -> AuthorizationContext:
    if credentials is None or credentials.scheme.lower() != "bearer": raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try: return get_auth_provider().get_context(credentials.credentials)
    except (SupabaseAuthenticationError, SupabaseAuthConfigurationError) as exc: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed") from exc


@lru_cache(maxsize=1)
def get_authorized_runtime() -> AuthorizedModelRuntime:
    providers = ProviderRegistry()
    provider_name = os.getenv("AI_PLATFORM_PROVIDER", "openai-compatible").strip().lower()
    if provider_name not in ("openai-compatible", "openai", "xai", "ollama"): raise RuntimeError("No configured provider")
    from ai_platform.providers.openai_compatible import OpenAICompatibleProvider
    if provider_name == "ollama":
        base_url = (os.getenv("OPENAI_BASE_URL") or os.getenv("OLLAMA_BASE_URL") or "http://127.0.0.1:11434/v1").strip()
        api_key = (os.getenv("OLLAMA_API_KEY") or os.getenv("OPENAI_API_KEY") or "ollama").strip()
    else:
        base_url, api_key = _resolve_cloud_provider_credentials()
    is_local = _is_loopback_base_url(base_url)
    if not api_key and not is_local: raise RuntimeError("Provider API key is required")
    if provider_name == "ollama" and not is_local: raise RuntimeError("Ollama provider is restricted to loopback URLs")
    providers.register(OpenAICompatibleProvider(api_key=api_key or None, base_url=base_url,
                                                timeout_seconds=float(os.getenv("AI_PLATFORM_PROVIDER_TIMEOUT_SECONDS", "120"))))
    model_runtime = ModelRuntime(providers)
    client = get_supabase_server_client()
    return AuthorizedModelRuntime(
        model_runtime,
        run_engine=RunEngine(model_runtime, SupabaseRunStore(client), RateLimitPolicy(SupabaseRateLimitStore(client))),
        model_registry=get_model_registry(),
        approval_service=ApprovalService(client),
    )


def require_runtime() -> AuthorizedModelRuntime:
    try: return get_authorized_runtime()
    except Exception as exc: raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model provider is not configured") from exc
