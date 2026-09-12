import pytest

from ai_platform.config import validate_provider_base_url


def test_ollama_loopback_url_allowed():
    assert validate_provider_base_url("http://127.0.0.1:11434/v1").endswith("11434/v1")
    assert validate_provider_base_url("http://localhost:11434/v1")


def test_remote_http_ollama_rejected_by_url_rules():
    with pytest.raises(ValueError):
        validate_provider_base_url("http://evil.example:11434/v1")


def test_get_authorized_runtime_ollama_requires_loopback(monkeypatch):
    monkeypatch.setenv("AI_PLATFORM_PROVIDER", "ollama")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.com/v1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from api import dependencies

    dependencies.get_authorized_runtime.cache_clear()
    with pytest.raises(Exception):
        dependencies.get_authorized_runtime()
    dependencies.get_authorized_runtime.cache_clear()
