"""Tests for pipeline_runner — core pipeline orchestration.

Focuses on the _api, _wait_job, and _latest_idea_id helpers
as well as the router error paths. Uses mock to avoid real HTTP calls.
"""

from __future__ import annotations

import json
import time
import uuid
from unittest.mock import MagicMock, patch

import pytest
from urllib.error import HTTPError

from backend.app.admin_boundary import ADMIN_IDENTITY_HEADER, ADMIN_SIGNATURE_HEADER
from backend.app.pipeline_runner import (
    PipelineStep,
    _admin_headers,
    _api,
    _api_with_wait,
    _wait_job,
    _latest_idea_id,
    _skip_stage,
    create_pipeline_runner_router,
)
from backend.app.settings import Settings


# ── Fixtures ──


@pytest.fixture
def settings() -> Settings:
    s = Settings()
    s.admin_boundary_secret = "test-secret-for-pipeline-tests"
    return s


@pytest.fixture
def headers(settings: Settings) -> dict[str, str]:
    return _admin_headers(settings)


# ── _admin_headers tests ──


class TestAdminHeaders:
    def test_returns_required_keys(self, settings: Settings) -> None:
        hdrs = _admin_headers(settings, user_id="test_user")
        assert ADMIN_IDENTITY_HEADER in hdrs
        assert ADMIN_SIGNATURE_HEADER in hdrs
        assert "Content-Type" in hdrs
        assert hdrs["Content-Type"] == "application/json"

    def test_identity_payload_contains_user_id(self, settings: Settings) -> None:
        hdrs = _admin_headers(settings, user_id="custom_runner")
        payload = json.loads(hdrs[ADMIN_IDENTITY_HEADER])
        assert payload["user_id"] == "custom_runner"
        assert payload["email"] == "admin@example.com"

    def test_different_user_ids_produce_different_signatures(self, settings: Settings) -> None:
        h1 = _admin_headers(settings, user_id="user_a")
        h2 = _admin_headers(settings, user_id="user_b")
        assert h1[ADMIN_SIGNATURE_HEADER] != h2[ADMIN_SIGNATURE_HEADER]

    def test_default_user_id_is_pipeline_runner(self, settings: Settings) -> None:
        hdrs = _admin_headers(settings)
        payload = json.loads(hdrs[ADMIN_IDENTITY_HEADER])
        assert payload["user_id"] == "pipeline_runner"


# ── _api tests (mocked urlopen) ──


class MockResponse:
    """Helper: a real object that acts like an HTTP response for context manager."""

    def __init__(self, status: int, body_bytes: bytes):
        self.status = status
        self._body = body_bytes

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class MockHttpError(HTTPError):
    """Helper: a real HTTPError that carries a readable body."""

    def __init__(self, url: str, code: int, msg: str, body_bytes: bytes):
        super().__init__(url, code, msg, {}, None)
        self._body = body_bytes
        self.code = code

    def read(self) -> bytes:
        return self._body


class TestApi:
    def test_get_returns_status_and_json(self) -> None:
        with patch("backend.app.pipeline_runner.urlopen", return_value=MockResponse(200, b'{"key": "value"}')) as mock:
            status, body = _api("GET", "/test", headers={"Authorization": "Bearer x"})

        assert status == 200
        assert body == {"key": "value"}
        mock.assert_called_once()

    def test_post_with_body_sends_json(self) -> None:
        with patch("backend.app.pipeline_runner.urlopen", return_value=MockResponse(201, b'{"id": "abc"}')) as mock:
            status, body = _api("POST", "/create", {"name": "test"}, {"Authorization": "Bearer x"})

        assert status == 201
        assert body == {"id": "abc"}
        # Verify the request was built with data (not None)
        call_args, _call_kwargs = mock.call_args
        req = call_args[0]
        assert req.data is not None

    def test_empty_response_returns_none(self) -> None:
        with patch("backend.app.pipeline_runner.urlopen", return_value=MockResponse(204, b"")):
            status, body = _api("DELETE", "/resource/1")

        assert status == 204
        assert body is None

    def test_http_error_returns_code_and_parsed_json(self) -> None:
        exc = MockHttpError("http://test/404", 404, "Not Found", b'{"detail": "Not found"}')

        with patch("backend.app.pipeline_runner.urlopen", side_effect=exc):
            status, body = _api("GET", "/not-found")

        assert status == 404
        assert body == {"detail": "Not found"}

    def test_http_error_with_invalid_json_returns_raw_string(self) -> None:
        exc = MockHttpError("http://test/500", 500, "Error", b"Internal Server Error")

        with patch("backend.app.pipeline_runner.urlopen", side_effect=exc):
            status, body = _api("GET", "/error")

        assert status == 500
        assert body == "Internal Server Error"


# ── _wait_job tests ──


class TestWaitJob:
    def test_returns_when_job_completed(self, headers: dict) -> None:
        responses = [
            (200, {"status": "running"}),
            (200, {"status": "running"}),
            (200, {"status": "completed"}),
        ]
        mock_api = MagicMock(side_effect=responses)

        with patch("backend.app.pipeline_runner._api", mock_api):
            # Should not raise
            _wait_job("task_1", "Test job", headers)

        assert mock_api.call_count == 3

    def test_raises_on_job_failure(self, headers: dict) -> None:
        with patch("backend.app.pipeline_runner._api", return_value=(200, {"status": "failed", "error_message": "Something broke"})):
            with pytest.raises(RuntimeError, match="Test job: job failed"):
                _wait_job("task_fail", "Test job", headers)

    def test_raises_on_non_200_status(self, headers: dict) -> None:
        with patch("backend.app.pipeline_runner._api", return_value=(404, {"detail": "Not found"})):
            with pytest.raises(RuntimeError, match="Test job: job status"):
                _wait_job("task_missing", "Test job", headers)

    def test_raises_timeout_when_job_stalls(self, headers: dict) -> None:
        with patch("backend.app.pipeline_runner._api", return_value=(200, {"status": "running"})):
            with patch("backend.app.pipeline_runner.JOB_TIMEOUT_SEC", 0.1):
                with patch("backend.app.pipeline_runner.POLL_INTERVAL_SEC", 0.05):
                    with pytest.raises(TimeoutError, match="Test job: timed out"):
                        _wait_job("task_stall", "Test job", headers)


# ── _api_with_wait tests ──


class TestApiWithWait:
    def test_sync_200_returns_body(self, headers: dict) -> None:
        with patch("backend.app.pipeline_runner._api", return_value=(200, {"result": "ok"})):
            result = _api_with_wait("GET", "/sync", None, "Sync", headers)
        assert result == {"result": "ok"}

    def test_async_202_polls_then_returns_none(self, headers: dict) -> None:
        """202 with task_id should trigger wait and return None."""
        call_count = 0

        def mock_api(method, path, body=None, **kw):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return (202, {"detail": {"task_id": "async_task_1"}})
            if call_count == 2:
                return (200, {"status": "completed"})
            return (200, {"status": "completed"})

        with patch("backend.app.pipeline_runner._api", mock_api):
            result = _api_with_wait("POST", "/async", {}, "Async", headers)
        assert result is None

    def test_202_without_task_id_raises(self, headers: dict) -> None:
        with patch("backend.app.pipeline_runner._api", return_value=(202, {"detail": {"no_task": True}})):
            with pytest.raises(RuntimeError, match="Async: 202 with no task_id"):
                _api_with_wait("POST", "/async", {}, "Async", headers)

    def test_error_status_4xx_raises(self, headers: dict) -> None:
        with patch("backend.app.pipeline_runner._api", return_value=(422, {"detail": "Validation error"})):
            with pytest.raises(RuntimeError, match="Label: HTTP 422"):
                _api_with_wait("POST", "/bad", {}, "Label", headers)


# ── _latest_idea_id tests ──


class TestLatestIdeaId:
    def test_returns_latest_created_idea(self, headers: dict) -> None:
        ideas = [
            {"id": "old", "created_at": "2024-01-01T00:00:00"},
            {"id": "newest", "created_at": "2025-06-01T00:00:00"},
            {"id": "middle", "created_at": "2024-06-01T00:00:00"},
        ]
        with patch("backend.app.pipeline_runner._api", return_value=(200, ideas)):
            assert _latest_idea_id(headers) == "newest"

    def test_raises_on_empty_list(self, headers: dict) -> None:
        with patch("backend.app.pipeline_runner._api", return_value=(200, [])):
            with pytest.raises(RuntimeError, match="List ideas"):
                _latest_idea_id(headers)

    def test_raises_on_http_error(self, headers: dict) -> None:
        with patch("backend.app.pipeline_runner._api", return_value=(500, {"detail": "DB error"})):
            with pytest.raises(RuntimeError, match="List ideas"):
                _latest_idea_id(headers)

    def test_handles_ideas_without_created_at(self, headers: dict) -> None:
        """Ideas missing created_at should be sorted to the beginning and not error."""
        ideas = [
            {"id": "no_date"},
            {"id": "with_date", "created_at": "2025-01-01T00:00:00"},
        ]
        with patch("backend.app.pipeline_runner._api", return_value=(200, ideas)):
            # max() with key will crash if a dict lacks 'created_at'
            assert _latest_idea_id(headers) == "with_date"


# ── PipelineStep model tests ──


class TestPipelineStep:
    def test_default_fields(self) -> None:
        step = PipelineStep(label="Test", status="pending")
        assert step.status == "pending"
        assert step.detail is None

    def test_can_set_status_and_detail(self) -> None:
        step = PipelineStep(label="Test", status="running", detail="Working")
        assert step.status == "running"
        assert step.detail == "Working"

    def test_all_statuses_valid(self) -> None:
        for status in ("pending", "running", "done", "skipped", "failed"):
            step = PipelineStep(label="Test", status=status)
            assert step.status == status


# ── _skip_stage tests ──


class TestSkipStage:
    def test_appends_two_skipped_steps(self) -> None:
        steps: list[PipelineStep] = []
        _skip_stage(steps, "Approve Test", "Run Test")
        assert len(steps) == 2
        assert steps[0].status == "skipped"
        assert steps[0].detail == "Already done"
        assert steps[1].status == "skipped"
        assert steps[1].detail == "Already done"

    def test_skipped_steps_have_labels(self) -> None:
        steps: list[PipelineStep] = []
        _skip_stage(steps, "Approve Outline", "Generate Draft")
        assert steps[0].label == "Approve Outline"
        assert steps[1].label == "Generate Draft"


# ── Router creation tests ──


class TestCreateRouter:
    def test_router_created_with_correct_prefix(self, settings: Settings) -> None:
        router = create_pipeline_runner_router(settings)
        assert router.prefix == "/admin/pipeline"
        assert len(router.routes) == 1

    def test_router_has_run_endpoint(self, settings: Settings) -> None:
        router = create_pipeline_runner_router(settings)
        routes = [r for r in router.routes if hasattr(r, "path") and "/run" in r.path]
        assert len(routes) >= 1
        route = routes[0]
        methods = getattr(route, "methods", set())
        assert "POST" in methods


# ── In-memory settings tests (no external dependencies) ──


class TestSettingsInteraction:
    def test_settings_used_correctly(self) -> None:
        """Verify settings are read correctly by pipeline runner helpers."""
        s = Settings()
        s.admin_boundary_secret = "custom-secret-12345"
        hdrs = _admin_headers(s, user_id="verify")
        payload = json.loads(hdrs[ADMIN_IDENTITY_HEADER])
        assert payload["user_id"] == "verify"

    def test_different_secrets_produce_different_signatures(self) -> None:
        s1 = Settings()
        s1.admin_boundary_secret = "secret-1"
        s2 = Settings()
        s2.admin_boundary_secret = "secret-2"
        h1 = _admin_headers(s1, user_id="same_user")
        h2 = _admin_headers(s2, user_id="same_user")
        assert h1[ADMIN_SIGNATURE_HEADER] != h2[ADMIN_SIGNATURE_HEADER]
