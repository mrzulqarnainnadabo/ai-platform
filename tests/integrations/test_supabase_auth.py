from types import SimpleNamespace

import pytest

from ai_platform.integrations.supabase_auth import (
    SupabaseAuthContextProvider,
    SupabaseAuthenticationError,
)
from ai_platform.policy.capabilities import Capability


class FakeAuth:
    def __init__(self, claims=None, error=None):
        self.claims = claims
        self.error = error

    def get_claims(self, jwt):
        assert jwt == "valid-token"
        if self.error:
            raise self.error
        return SimpleNamespace(data={"claims": self.claims})


class FakeClient:
    def __init__(self, claims=None, error=None):
        self.auth = FakeAuth(claims=claims, error=error)


def valid_claims(**overrides):
    claims = {
        "sub": "user-1",
        "aud": "authenticated",
        "is_anonymous": False,
        "ai_platform_tenant_id": "tenant-1",
        "ai_platform_permissions": ["model.generate"],
    }
    claims.update(overrides)
    return claims


def test_verified_claims_map_to_platform_authorization():
    provider = SupabaseAuthContextProvider(FakeClient(valid_claims()))

    context = provider.get_context("valid-token")

    assert context.identity.subject == "user-1"
    assert context.identity.tenant_id == "tenant-1"
    assert context.permissions.allows(Capability.MODEL_GENERATE)
    assert not context.permissions.allows(Capability.MODEL_STREAM)


def test_missing_tenant_fails_closed():
    provider = SupabaseAuthContextProvider(FakeClient(valid_claims(ai_platform_tenant_id=None)))

    with pytest.raises(SupabaseAuthenticationError):
        provider.get_context("valid-token")


def test_anonymous_session_is_rejected():
    provider = SupabaseAuthContextProvider(FakeClient(valid_claims(is_anonymous=True)))

    with pytest.raises(SupabaseAuthenticationError):
        provider.get_context("valid-token")


def test_wrong_audience_is_rejected():
    provider = SupabaseAuthContextProvider(FakeClient(valid_claims(aud="anon")))

    with pytest.raises(SupabaseAuthenticationError):
        provider.get_context("valid-token")


def test_unknown_permissions_are_ignored_not_granted():
    provider = SupabaseAuthContextProvider(
        FakeClient(valid_claims(ai_platform_permissions=["model.generate", "admin.root", "malformed"]))
    )

    context = provider.get_context("valid-token")

    assert context.permissions.allows(Capability.MODEL_GENERATE)
    assert len(context.permissions.capabilities) == 1


def test_app_metadata_is_supported_but_user_metadata_is_not():
    provider = SupabaseAuthContextProvider(
        FakeClient(
            {
                "sub": "user-1",
                "aud": "authenticated",
                "is_anonymous": False,
                "app_metadata": {
                    "ai_platform_tenant_id": "tenant-2",
                    "ai_platform_permissions": ["model.stream"],
                },
                "user_metadata": {
                    "ai_platform_tenant_id": "attacker-tenant",
                    "ai_platform_permissions": ["model.generate"],
                },
            }
        )
    )

    context = provider.get_context("valid-token")

    assert context.identity.tenant_id == "tenant-2"
    assert context.permissions.allows(Capability.MODEL_STREAM)
    assert not context.permissions.allows(Capability.MODEL_GENERATE)
