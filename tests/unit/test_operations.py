from ai_platform.health import HealthStatus, liveness, readiness
from ai_platform.observability import InMemoryEventSink, RuntimeEvent, sanitize


def test_liveness_is_independent_of_provider():
    assert liveness("0.1.0").status == HealthStatus.HEALTHY


def test_readiness_can_report_provider_failure():
    assert readiness(provider_check=lambda: False).status == HealthStatus.NOT_READY


def test_observability_removes_sensitive_fields():
    safe = sanitize({"trace_id": "t", "prompt": "secret", "api_key": "secret", "latency_ms": 4})
    assert safe == {"trace_id": "t", "latency_ms": 4}
    sink = InMemoryEventSink(); sink.emit(RuntimeEvent("complete", "t", {"response": "secret", "status": "ok"}))
    assert "response" not in sink.events[0].metadata
