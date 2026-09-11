"""Supabase Auth adapter for the application boundary."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from supabase import Client, create_client

from ai_platform.policy.authorization import AuthorizationContext, Identity, Permissions
from ai_platform.policy.capabilities import Capability, parse_capability


class SupabaseAuthenticationError(RuntimeError):
    """Raised when a Supabase access token cannot be trusted."""


class SupabaseAuthContextProvider:
    """Verify Supabase JWTs and map only trusted claims to platform authorization."""

    def __init__(self, client: Client, *, tenant_claim: str = "ai_platform_tenant_id",
                 permissions_claim: str = "ai_platform_permissions") -> None:
        self._client = client
        self._tenant_claim = tenant_claim
        self._permissions_claim = permissions_claim

    @classmethod
    def from_environment(cls) -> "SupabaseAuthContextProvider":
        url = os.getenv("SUPABASE_URL", "").strip()
        key = os.getenv("SUPABASE_PUBLISHABLE_KEY", "").strip()
        if not url or not key:
            raise SupabaseAuthConfigurationError(
                "SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY are required"
            )
        return cls(
            create_client(url, key),
            tenant_claim=os.getenv("AI_PLATFORM_TENANT_CLAIM", "ai_platform_tenant_id").strip()
            or "ai_platform_tenant_id",
            permissions_claim=os.getenv("AI_PLATFORM_PERMISSIONS_CLAIM", "ai_platform_permissions").strip()
            or "ai_platform_permissions",
        )

    def get_context(self, access_token: str) -> AuthorizationContext:
        token = access_token.strip()
        if not token:
            raise SupabaseAuthenticationError("Missing access token")

        try:
            response = self._client.auth.get_claims(jwt=token)
        except Exception as exc:
            raise SupabaseAuthenticationError("Invalid or unverifiable access token") from exc

        claims = _claims_from_response(response)
        if not claims:
            raise SupabaseAuthenticationError("Invalid or unverifiable access token")

        subject = _required_string(claims.get("sub"))
        if not subject:
            raise SupabaseAuthenticationError("Access token has no subject")

        if not _audience_is_authenticated(claims.get("aud")):
            raise SupabaseAuthenticationError("Access token audience is not authenticated")

        if bool(claims.get("is_anonymous", False)):
            raise SupabaseAuthenticationError("Anonymous Supabase sessions cannot access the platform")

        tenant_id = _trusted_claim(claims, self._tenant_claim)
        if not isinstance(tenant_id, str) or not tenant_id:
            raise SupabaseAuthenticationError("Access token has no platform tenant")

        permissions = _permission_values(_trusted_claim(claims, self._permissions_claim))
        capabilities = frozenset(
            capability
            for value in permissions
            if (capability := _safe_capability(value)) is not None
        )

        return AuthorizationContext(
            identity=Identity(subject=subject, tenant_id=tenant_id),
            permissions=Permissions(capabilities=capabilities),
        )


@dataclass(frozen=True)
class SupabaseAuthConfigurationError(RuntimeError):
    """Raised when application Supabase auth configuration is incomplete."""

    message: str

    def __str__(self) -> str:
        return self.message


def _claims_from_response(response: Any) -> Mapping[str, Any]:
    data = getattr(response, "data", response)
    if isinstance(data, Mapping):
        claims = data.get("claims", data)
        return claims if isinstance(claims, Mapping) else {}
    return {}


def _trusted_claim(claims: Mapping[str, Any], name: str) -> Optional[str | list[str]]:
    value = claims.get(name)
    if value is None:
        app_metadata = claims.get("app_metadata")
        if isinstance(app_metadata, Mapping):
            value = app_metadata.get(name)
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return [item.strip() for item in value if item.strip()]
    return None


def _permission_values(value: Optional[str | list[str]]) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(item.strip() for item in value.split(",") if item.strip())
    return tuple(item for item in value if item)


def _safe_capability(value: str) -> Optional[Capability]:
    try:
        return parse_capability(value)
    except (ValueError, TypeError):
        return None


def _required_string(value: Any) -> Optional[str]:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _audience_is_authenticated(audience: Any) -> bool:
    if isinstance(audience, str):
        return audience == "authenticated"
    if isinstance(audience, list):
        return "authenticated" in audience
    return False
