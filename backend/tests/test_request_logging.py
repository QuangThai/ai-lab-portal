import json
import logging

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.settings import Settings


def test_request_id_header_is_reused_and_logged(caplog: pytest.LogCaptureFixture) -> None:
    client = TestClient(create_app(Settings(environment="test")))

    with caplog.at_level(logging.INFO, logger="ai_lab_portal.request"):
        response = client.get("/health", headers={"x-request-id": "req-test-123"})

    assert response.headers["x-request-id"] == "req-test-123"
    log_payloads = [json.loads(record.message) for record in caplog.records]
    assert len(log_payloads) == 1
    log_payload = log_payloads[0]
    assert log_payload["level"] == "INFO"
    assert log_payload["request_id"] == "req-test-123"
    assert log_payload["method"] == "GET"
    assert log_payload["path"] == "/health"
    assert log_payload["status_code"] == 200
    assert log_payload["action"] == "http_request"
    assert log_payload["message"] == "GET /health completed with 200"
    assert log_payload["duration_ms"] >= 0
    assert log_payload["timestamp"]
    assert "authorization" not in caplog.text.lower()


def test_request_id_header_is_generated_when_missing() -> None:
    client = TestClient(create_app(Settings(environment="test")))

    response = client.get("/health")

    assert response.headers["x-request-id"]
