"""Phase 1 API smoke tests."""

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def client() -> TestClient:
    app = create_app(Settings(environment="test", app_name="test-lead-agent"))
    return TestClient(app)


def test_health_returns_service_status_and_request_id() -> None:
    response = client().get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "test-lead-agent",
        "environment": "test",
    }
    assert response.headers["X-Request-ID"]


def test_health_preserves_a_valid_supplied_request_id() -> None:
    response = client().get("/api/v1/health/live", headers={"X-Request-ID": "upstream-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "upstream-123"


def test_readiness_endpoint_is_versioned() -> None:
    response = client().get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_unknown_route_uses_standard_error_envelope() -> None:
    response = client().get("/api/v1/unknown")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "HTTP_ERROR"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]
