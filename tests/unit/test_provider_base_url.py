"""SSRF and base_url validation for the OpenAI-compatible adapter."""
import pytest

from ai_platform.providers.openai_compatible import _validate_provider_base_url, OpenAICompatibleProvider


def test_allows_public_https():
    assert _validate_provider_base_url("https://api.openai.com/v1") == "https://api.openai.com/v1"
    assert _validate_provider_base_url("https://api.x.ai/v1") == "https://api.x.ai/v1"


def test_allows_loopback_http():
    assert _validate_provider_base_url("http://localhost:8080/v1") == "http://localhost:8080/v1"
    assert _validate_provider_base_url("http://127.0.0.1:11434") == "http://127.0.0.1:11434"


def test_rejects_http_non_loopback():
    with pytest.raises(ValueError, match="HTTPS"):
        _validate_provider_base_url("http://example.com/v1")


def test_rejects_private_and_metadata_ips():
    for bad in (
        "https://169.254.169.254/latest/meta-data",
        "https://10.0.0.1/v1",
        "https://192.168.1.1/v1",
        "https://172.16.0.1/v1",
    ):
        with pytest.raises(ValueError, match="private|link-local|reserved"):
            _validate_provider_base_url(bad)


def test_rejects_empty_and_bad_scheme():
    with pytest.raises(ValueError):
        _validate_provider_base_url("")
    with pytest.raises(ValueError):
        _validate_provider_base_url("ftp://api.openai.com/v1")


def test_provider_init_uses_validator():
    with pytest.raises(ValueError, match="private|link-local|reserved"):
        OpenAICompatibleProvider(api_key="k", base_url="https://10.0.0.5/v1")
