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
    assert "authentication" in body


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


def test_public_landing_is_html_and_crawlable():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "AI Platform" in response.text
    assert "og:title" in response.text
    assert "lang=\"en\"" in response.text


def test_robots_allows_public_disallows_model_api():
    response = client.get("/robots.txt")
    assert response.status_code == 200
    text = response.text
    assert "Allow: /" in text
    assert "Disallow: /api/v1/" in text
    assert "Sitemap:" in text


def test_sitemap_lists_public_routes():
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert "<urlset" in response.text
    assert "/docs" in response.text
    assert "/api/v1/" not in response.text  # model APIs not advertised in sitemap


def test_openapi_docs_available():
    response = client.get("/docs")
    assert response.status_code == 200
    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    schema = openapi.json()
    assert schema["info"]["title"] == "AI Platform"
    assert "components" in schema
    assert "securitySchemes" in schema["components"]
