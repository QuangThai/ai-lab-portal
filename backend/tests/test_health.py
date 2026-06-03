from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.settings import Settings


def test_health_endpoint_returns_service_status() -> None:
    client = TestClient(create_app(Settings(environment="test")))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "ai-lab-portal-api",
        "status": "ok",
        "environment": "test",
    }


def test_openapi_docs_are_available_in_development() -> None:
    client = TestClient(create_app(Settings(environment="test")))

    response = client.get("/docs")

    assert response.status_code == 200
    assert "Swagger UI" in response.text
