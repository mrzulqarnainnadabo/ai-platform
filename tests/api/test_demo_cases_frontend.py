from api.demo_cases_frontend import demo_cases_page, demo_mode_enabled


def test_demo_mode_requires_explicit_non_production_gate(monkeypatch):
    monkeypatch.delenv("AI_PLATFORM_DEMO_MODE", raising=False)
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    assert demo_mode_enabled() is False

    monkeypatch.setenv("AI_PLATFORM_DEMO_MODE", "true")
    assert demo_mode_enabled() is True


def test_demo_mode_is_disabled_in_vercel_production(monkeypatch):
    monkeypatch.setenv("AI_PLATFORM_DEMO_MODE", "true")
    monkeypatch.setenv("VERCEL_ENV", "production")
    assert demo_mode_enabled() is False
    assert demo_cases_page().status_code == 404


def test_demo_mode_is_disabled_in_explicit_production_environment(monkeypatch):
    monkeypatch.setenv("AI_PLATFORM_DEMO_MODE", "true")
    monkeypatch.setenv("ENVIRONMENT", "production")
    assert demo_mode_enabled() is False
    assert demo_cases_page().status_code == 404


def test_demo_page_contains_only_fixed_demo_identity_and_no_server_secrets(monkeypatch):
    monkeypatch.setenv("AI_PLATFORM_DEMO_MODE", "true")
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "server-secret-must-not-appear")
    monkeypatch.setenv("XAI_API_KEY", "model-secret-must-not-appear")

    body = demo_cases_page().body.decode("utf-8")

    assert "DEMO MODE — DEVELOPMENT ONLY" in body
    assert "demo.operator@local.invalid" in body
    assert "demo-tenant" in body
    assert "server-secret-must-not-appear" not in body
    assert "model-secret-must-not-appear" not in body


def test_demo_page_reuses_the_real_case_workspace(monkeypatch):
    monkeypatch.setenv("AI_PLATFORM_DEMO_MODE", "true")
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)

    body = demo_cases_page().body.decode("utf-8")

    assert "Intelligence Cases" in body
    assert "Run AI triage" in body
    assert "Attach evidence" in body
    assert "Immutable Audit Ledger" in body
