"""SSRF and base_url validation (shared library rule)."""
import pytest

from ai_platform.config import validate_provider_base_url, ProviderConfig
from ai_platform.providers.openai_compatible import OpenAICompatibleProvider


def test_allows_public_https():
    assert validate_provider_base_url("https://api.openai.com/v1") == "https://api.openai.com/v1"
    assert validate_provider_base_url("https://api.x.ai/v1") == "https://api.x.ai/v1"


def test_allows_loopback_http():
    assert validate_provider_base_url("http://localhost:8080/v1") == "http://localhost:8080/v1"
    assert validate_provider_base_url("http://127.0.0.1:11434") == "http://127.0.0.1:11434"


def test_rejects_http_non_loopback():
    with pytest.raises(ValueError, match="HTTPS"):
        validate_provider_base_url("http://example.com/v1")


def test_rejects_private_and_metadata_ips():
    for bad in (
        "https://169.254.169.254/latest/meta-data",
        "https://10.0.0.1/v1",
        "https://192.168.1.1/v1",
        "https://172.16.0.1/v1",
        "https://2852039166/v1",  # 169.254.169.254 encoded as integer
        "http://017700000001/v1",  # 127.0.0.1 in octal - rejected because HTTP requires explicit localhost/127.0.0.1
    ):
        if "017700000001" in bad and "http://" in bad:
            with pytest.raises(ValueError, match="HTTPS"):
                validate_provider_base_url(bad)
        else:
            with pytest.raises(ValueError, match="private|link-local|reserved"):
                validate_provider_base_url(bad)


def test_rejects_empty_and_bad_scheme():
    with pytest.raises(ValueError):
        validate_provider_base_url("")
    with pytest.raises(ValueError):
        validate_provider_base_url("ftp://api.openai.com/v1")


def test_provider_init_uses_shared_validator():
    with pytest.raises(ValueError, match="private|link-local|reserved"):
        OpenAICompatibleProvider(api_key="k", base_url="https://10.0.0.5/v1")


def test_provider_config_uses_shared_validator():
    with pytest.raises(ValueError, match="private|link-local|reserved"):
        ProviderConfig("openai-compatible", "m", "https://10.0.0.5/v1")
    cfg = ProviderConfig("openai-compatible", "m", "https://api.openai.com/v1/")
    assert cfg.base_url == "https://api.openai.com/v1"
