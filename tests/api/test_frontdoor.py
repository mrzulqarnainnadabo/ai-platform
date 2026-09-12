"""Regression tests for the minimal browser front door."""

from fastapi.testclient import TestClient

from api.frontdoor import app


def test_frontdoor_is_public_and_contains_auth_ui(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "publishable-example")

    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert "Sign in" in response.text
    assert "Create an account" in response.text
    assert "/api/v1/models/generate" in response.text
    assert "OPENAI_API_KEY" not in response.text
    assert "XAI_API_KEY" not in response.text


def test_frontdoor_reports_missing_browser_auth_configuration(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_PUBLISHABLE_KEY", raising=False)

    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert "SUPABASE_URL" in response.text
    assert "SUPABASE_PUBLISHABLE_KEY" in response.text
