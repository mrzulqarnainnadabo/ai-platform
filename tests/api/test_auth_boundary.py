from fastapi.testclient import TestClient

from api.dependencies import require_auth, require_runtime
from api.index import app
from ai_platform.core.messages import Message, Role
from ai_platform.core.response import FinishReason, ModelResponse, TokenUsage
from ai_platform.policy.authorization import AuthorizationContext, Identity, Permissions
from ai_platform.policy.capabilities import Capability
from ai_platform.runtime.authorized import AuthorizedModelRuntime
from ai_platform.runtime.model_runtime import RuntimeResult


class FakeRuntime:
    async def generate(self, messages, config, provider, context=None):
        assert provider == "openai-compatible"
        return RuntimeResult(ModelResponse(message=Message(Role.ASSISTANT, "hello"), finish_reason=FinishReason.STOP,
            usage=TokenUsage(), model_name=config.model_name, provider_name=provider, response_id="response-1"),
            {"trace_id": context.trace_id if context else "trace-1"})

    async def stream(self, messages, config, provider, context=None):
        assert provider == "openai-compatible"
        yield RuntimeResult(ModelResponse(message=Message(Role.ASSISTANT, "hello"), finish_reason=FinishReason.STOP,
            usage=TokenUsage(), model_name=config.model_name, provider_name=provider, response_id="stream-1"),
            {"trace_id": context.trace_id if context else "trace-stream"})


class NonExecutingRuntime:
    async def generate(self, *args, **kwargs): raise AssertionError("provider runtime must not execute after policy denial")
    async def stream(self, *args, **kwargs):
        raise AssertionError("provider runtime must not execute after policy denial")
        yield  # pragma: no cover


class FakeRunEngine:
    def __init__(self, runtime): self.runtime = runtime
    async def generate(self, *, messages, config, model_policy, tenant_id, subject_id, context=None):
        return await self.runtime.generate(messages, config, model_policy.provider, context)
    async def stream(self, *, messages, config, model_policy, tenant_id, subject_id, context=None):
        async for result in self.runtime.stream(messages, config, model_policy.provider, context):
            yield result


def governed(runtime):
    return AuthorizedModelRuntime(runtime, run_engine=FakeRunEngine(runtime))


def auth_context():
    return AuthorizationContext(identity=Identity(subject="user-1", tenant_id="tenant-1"), permissions=Permissions(frozenset({Capability.MODEL_GENERATE})))


def auth_context_stream():
    return AuthorizationContext(identity=Identity(subject="user-1", tenant_id="tenant-1"), permissions=Permissions(frozenset({Capability.MODEL_STREAM})))


def auth_context_without_generate():
    return AuthorizationContext(identity=Identity(subject="user-1", tenant_id="tenant-1"), permissions=Permissions(frozenset()))


def test_health_remains_public():
    assert TestClient(app).get("/api/health/live").status_code == 200


def test_model_endpoint_requires_bearer_token():
    assert TestClient(app).post("/api/v1/models/generate", json={"model_name": "fast-general", "messages": [{"role": "user", "content": "hi"}]}).status_code == 401


def test_stream_endpoint_requires_bearer_token():
    assert TestClient(app).post("/api/v1/models/stream", json={"model_name": "fast-general", "messages": [{"role": "user", "content": "hi"}]}).status_code == 401


def test_model_endpoint_uses_verified_auth_and_runtime():
    app.dependency_overrides[require_auth] = lambda: auth_context(); app.dependency_overrides[require_runtime] = lambda: governed(FakeRuntime())
    try:
        response = TestClient(app).post("/api/v1/models/generate", json={"model_name": "fast-general", "messages": [{"role": "user", "content": "hi"}]})
        assert response.status_code == 200
        body = response.json(); assert body["id"] == "response-1"; assert body["trace_id"]; assert body["message"]["role"] == "assistant"
    finally: app.dependency_overrides.clear()


def test_stream_endpoint_uses_verified_auth_and_runtime():
    app.dependency_overrides[require_auth] = lambda: auth_context_stream(); app.dependency_overrides[require_runtime] = lambda: governed(FakeRuntime())
    try:
        response = TestClient(app).post("/api/v1/models/stream", json={"model_name": "fast-general", "messages": [{"role": "user", "content": "hi"}]})
        assert response.status_code == 200; assert "text/event-stream" in response.headers.get("content-type", ""); assert "data:" in response.text; assert "[DONE]" in response.text
    finally: app.dependency_overrides.clear()


def test_model_endpoint_does_not_accept_client_supplied_authorization():
    app.dependency_overrides[require_auth] = lambda: auth_context(); app.dependency_overrides[require_runtime] = lambda: governed(FakeRuntime())
    try:
        response = TestClient(app).post("/api/v1/models/generate", json={"model_name": "fast-general", "provider": "attacker-provider",
            "messages": [{"role": "user", "content": "hi"}], "tenant_id": "attacker-tenant", "permissions": ["model.generate"]})
        assert response.status_code == 200
    finally: app.dependency_overrides.clear()


def test_model_endpoint_denies_missing_capability_before_runtime():
    app.dependency_overrides[require_auth] = lambda: auth_context_without_generate(); app.dependency_overrides[require_runtime] = lambda: AuthorizedModelRuntime(NonExecutingRuntime())
    try:
        response = TestClient(app).post("/api/v1/models/generate", json={"model_name": "fast-general", "messages": [{"role": "user", "content": "hi"}]})
        assert response.status_code == 403; assert response.json()["detail"] == "Model capability denied"
    finally: app.dependency_overrides.clear()


def test_stream_endpoint_denies_missing_capability_before_runtime():
    app.dependency_overrides[require_auth] = lambda: auth_context_without_generate(); app.dependency_overrides[require_runtime] = lambda: AuthorizedModelRuntime(NonExecutingRuntime())
    try:
        response = TestClient(app).post("/api/v1/models/stream", json={"model_name": "fast-general", "messages": [{"role": "user", "content": "hi"}]})
        assert response.status_code == 403; assert response.json()["detail"] == "Model capability denied"
    finally: app.dependency_overrides.clear()
