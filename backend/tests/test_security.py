"""Tests for rate limiting and security headers."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    sign_admin_identity,
)
from backend.app.main import create_app
from backend.app.settings import Settings

TEST_SECRET = "test-admin-boundary-secret-at-least-32-chars"


def _test_settings() -> Settings:
    return Settings(environment="test", admin_boundary_secret=TEST_SECRET)


def _admin_headers() -> dict[str, str]:
    payload = json.dumps(
        {
            "user_id": "user_123",
            "email": "admin@example.com",
            "role": "admin",
            "issued_at": int(datetime.now(UTC).timestamp()),
        }
    )
    return {
        ADMIN_IDENTITY_HEADER: payload,
        ADMIN_SIGNATURE_HEADER: sign_admin_identity(payload, TEST_SECRET),
    }


# ===========================================================================
# Security headers
# ===========================================================================


class TestSecurityHeaders:
    """Verify security headers are set on responses."""

    def test_security_headers_present(self):
        """Admin responses include security headers."""
        settings = _test_settings()
        app = create_app(settings)
        client = TestClient(app)

        # Register the middlware in the test app
        from backend.app.security import add_security_headers_middleware

        add_security_headers_middleware(app)

        response = client.get("/admin/news/review-items", headers=_admin_headers())
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"
        assert response.headers.get("x-xss-protection") == "1; mode=block"
        assert "referrer-policy" in response.headers

    def test_rate_limiter_rejects_after_limit(self):
        """Rate limiter returns 429 after exceeding limit."""
        from backend.app.security import RateLimiter

        limiter = RateLimiter(max_requests=2, window_seconds=60)

        assert limiter.check("test-ip") is True  # 1st
        assert limiter.check("test-ip") is True  # 2nd
        assert limiter.check("test-ip") is False  # 3rd — blocked

    def test_rate_limiter_different_ips(self):
        """Different IPs have separate rate limit buckets."""
        from backend.app.security import RateLimiter

        limiter = RateLimiter(max_requests=1, window_seconds=60)

        assert limiter.check("ip-a") is True
        assert limiter.check("ip-b") is True  # Different IP, should be allowed
        assert limiter.check("ip-a") is False  # IP-A exceeded


# ===========================================================================
# Input validation
# ===========================================================================


class TestInputValidation:
    """Verify input validation on key endpoints."""

    def test_blog_idea_create_rejects_blank_title(self):
        """Blog idea creation rejects empty title."""
        from backend.app.blog_ideas import BlogIdeaCreate

        try:
            BlogIdeaCreate(
                title="",
                angle="Test",
                target_reader="Dev",
                article_goal="Test",
            )
            assert False, "Should have raised"
        except Exception:
            pass

    def test_blog_idea_create_rejects_empty_goal(self):
        """Blog idea creation rejects empty article_goal."""
        from backend.app.blog_ideas import BlogIdeaCreate

        try:
            BlogIdeaCreate(
                title="Test",
                angle="Test",
                target_reader="Dev",
                article_goal="",
            )
            assert False, "Should have raised"
        except Exception:
            pass

    def test_admin_boundary_rejects_expired(self):
        """Admin identity with expired timestamp is rejected."""
        from backend.app.admin_boundary import (
            parse_identity,
            sign_admin_identity,
        )

        payload = json.dumps({
            "user_id": "user_1",
            "email": "admin@example.com",
            "role": "admin",
            "issued_at": int(datetime.now(UTC).timestamp()) - 600,  # 10 min ago
        })
        sig = sign_admin_identity(payload, TEST_SECRET)
        settings = Settings(environment="test", admin_boundary_secret=TEST_SECRET)

        try:
            parse_identity(payload, sig, settings)
            assert False, "Should have raised for expired identity"
        except Exception:
            pass

    def test_admin_boundary_rejects_invalid_signature(self):
        """Admin identity with wrong signature is rejected."""
        from backend.app.admin_boundary import parse_identity

        payload = json.dumps({
            "user_id": "user_1",
            "email": "admin@example.com",
            "role": "admin",
            "issued_at": int(datetime.now(UTC).timestamp()),
        })
        settings = Settings(environment="test", admin_boundary_secret=TEST_SECRET)

        try:
            parse_identity(payload, "invalid_signature", settings)
            assert False, "Should have raised for invalid signature"
        except Exception:
            pass

    def test_security_module_imports(self):
        """Security module imports without error."""
        from backend.app.security import RateLimiter, add_security_headers_middleware, add_rate_limiting_middleware

        limiter = RateLimiter()
        assert limiter.max_requests == 60
        assert limiter.window_seconds == 60
