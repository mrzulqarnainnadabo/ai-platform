from api.dependencies import _resolve_cloud_provider_credentials


def test_xai_endpoint_prefers_xai_key_when_both_keys_are_configured(monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.x.ai/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("XAI_API_KEY", "xai-key")

    base_url, api_key = _resolve_cloud_provider_credentials()

    assert base_url == "https://api.x.ai/v1"
    assert api_key == "xai-key"


def test_openai_endpoint_prefers_openai_key_when_both_keys_are_configured(monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("XAI_API_KEY", "xai-key")

    base_url, api_key = _resolve_cloud_provider_credentials()

    assert base_url == "https://api.openai.com/v1"
    assert api_key == "openai-key"


def test_xai_endpoint_falls_back_to_openai_key_for_compatible_credentials(monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.x.ai/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-compatible-key")
    monkeypatch.delenv("XAI_API_KEY", raising=False)

    base_url, api_key = _resolve_cloud_provider_credentials()

    assert base_url == "https://api.x.ai/v1"
    assert api_key == "openai-compatible-key"
