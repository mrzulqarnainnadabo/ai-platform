from fastapi.testclient import TestClient

from api.index import app


client = TestClient(app)


def test_api_root_does_not_expose_model_execution():
    response = client.get("/api")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "foundation"
    assert body["model_execution"] == "protected-application-boundary-required"
    assert "endpoints" in body
    assert body["endpoints"]["generate"] == "POST /api/v1/models/generate"
    assert body["endpoints"]["stream"] == "POST /api/v1/models/stream"


def test_liveness_is_healthy():
    response = client.get("/api/health/live")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["checks"]["process"] == "up"


def test_readiness_is_healthy_without_external_provider_call():
    response = client.get("/api/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["checks"]["configuration"] == "valid"
