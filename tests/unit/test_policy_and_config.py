import pytest
from ai_platform.config import ProviderConfig
from ai_platform.policy import AuthorizationContext, Identity, Permissions, Capability, SimplePermissionEvaluator
from ai_platform.policy.decisions import Decision


def test_policy_is_deterministic_and_fail_closed():
    ctx = AuthorizationContext(Identity("u"), Permissions(frozenset({Capability.MODEL_GENERATE})))
    evaluator = SimplePermissionEvaluator()
    assert evaluator.evaluate(ctx, Capability.MODEL_GENERATE).decision == Decision.ALLOW
    assert evaluator.evaluate(ctx, Capability.MODEL_STREAM).decision == Decision.DENY


def test_provider_config_safe_public_dict():
    cfg = ProviderConfig("openai-compatible", "model", "https://api.openai.com/v1")
    public = cfg.to_public_dict()
    assert "super-secret" not in str(public)
    assert public["model_name"] == "model"


def test_provider_config_rejects_remote_http_and_metadata_ip():
    with pytest.raises(ValueError): ProviderConfig("x", "m", "http://example.com/v1")
    with pytest.raises(ValueError): ProviderConfig("x", "m", "http://169.254.169.254/latest")
