"""Tests for blog social features: reactions, bookmarks, stats.

Uses a seeded blog post + in-memory repos.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from time import time

import pytest
from fastapi.testclient import TestClient

from backend.app.admin_boundary import (
    USER_IDENTITY_HEADER,
    USER_SIGNATURE_HEADER,
    sign_admin_identity,
)
from backend.app.blog import BlogPost, BlogRepository
from backend.app.blog_social import InMemoryBlogSocialRepository
from backend.app.main import create_app
from backend.app.settings import Settings
from backend.app.user_profiles import InMemoryUserProfileRepository

TEST_SECRET = "test-admin-boundary-secret-at-least-32-chars"
POST_SLUG = "test-social-post"
ALLOWED_EMOJIS = {"👍", "❤️", "🚀", "👀", "🎯"}


@pytest.fixture
def shared_client() -> TestClient:
    """Create app with a seeded blog post + in-memory repos."""
    post = BlogPost(
        id="post_social_test",
        slug=POST_SLUG,
        title="Social Test Post",
        excerpt="Testing social features",
        content_markdown="# Social Test",
        author_name="Tester",
        status="published",
        published_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    blog_repo = BlogRepository(posts=[post])
    social_repo = InMemoryBlogSocialRepository()
    profiles = InMemoryUserProfileRepository()
    app = create_app(
        Settings(environment="test", admin_boundary_secret=TEST_SECRET),
        blog_repository=blog_repo,
        blog_social_repository=social_repo,
        user_profile_repository=profiles,
    )
    return TestClient(app)


def _headers(*, role: str, user_id: str = "user_123", email: str = "reader@example.com") -> dict[str, str]:
    payload = json.dumps(
        {"user_id": user_id, "email": email, "role": role, "issued_at": int(time())},
        separators=(",", ":"),
        sort_keys=True,
    )
    return {USER_IDENTITY_HEADER: payload, USER_SIGNATURE_HEADER: sign_admin_identity(payload, TEST_SECRET)}


# ── Reactions ──


class TestReactions:
    def test_toggle_adds_and_removes(self, shared_client: TestClient) -> None:
        client = shared_client
        # Add reaction
        res = client.post(
            f"/public/blog-posts/{POST_SLUG}/reactions",
            headers=_headers(role="user", user_id="reacter_a"),
            json={"emoji": "👍"},
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["user_reactions"]) >= 1

        # Toggle off (same emoji)
        res = client.post(
            f"/public/blog-posts/{POST_SLUG}/reactions",
            headers=_headers(role="user", user_id="reacter_a"),
            json={"emoji": "👍"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "👍" not in data["user_reactions"]

    def test_requires_auth(self, shared_client: TestClient) -> None:
        client = shared_client
        res = client.post(
            f"/public/blog-posts/{POST_SLUG}/reactions",
            json={"emoji": "👍"},
        )
        assert res.status_code == 401

    def test_different_emojis(self, shared_client: TestClient) -> None:
        client = shared_client
        for emoji in ALLOWED_EMOJIS:
            res = client.post(
                f"/public/blog-posts/{POST_SLUG}/reactions",
                headers=_headers(role="user", user_id=f"multi_reacter_{ord(emoji[0])}"),
                json={"emoji": emoji},
            )
            assert res.status_code == 200, f"Failed for emoji {emoji}"

    def test_invalid_emoji_returns_422(self, shared_client: TestClient) -> None:
        client = shared_client
        res = client.post(
            f"/public/blog-posts/{POST_SLUG}/reactions",
            headers=_headers(role="user"),
            json={"emoji": "invalid_emoji"},
        )
        assert res.status_code == 422

    def test_multiple_users_react(self, shared_client: TestClient) -> None:
        client = shared_client
        for uid in ("u_a", "u_b", "u_c"):
            res = client.post(
                f"/public/blog-posts/{POST_SLUG}/reactions",
                headers=_headers(role="user", user_id=uid),
                json={"emoji": "👍"},
            )
            assert res.status_code == 200

    def test_nonexistent_slug_does_not_crash(self, shared_client: TestClient) -> None:
        client = shared_client
        res = client.post(
            "/public/blog-posts/nonexistent-slug-999999/reactions",
            headers=_headers(role="user"),
            json={"emoji": "👍"},
        )
        assert res.status_code == 404


# ── Bookmarks ──


class TestBookmarks:
    def test_toggle(self, shared_client: TestClient) -> None:
        client = shared_client
        # Add bookmark
        res = client.post(
            f"/public/blog-posts/{POST_SLUG}/bookmarks",
            headers=_headers(role="user", user_id="bmark_user"),
        )
        assert res.status_code == 200
        assert res.json()["is_bookmarked"] is True

        # Toggle off
        res = client.post(
            f"/public/blog-posts/{POST_SLUG}/bookmarks",
            headers=_headers(role="user", user_id="bmark_user"),
        )
        assert res.status_code == 200
        assert res.json()["is_bookmarked"] is False

    def test_requires_auth(self, shared_client: TestClient) -> None:
        client = shared_client
        res = client.post(f"/public/blog-posts/{POST_SLUG}/bookmarks")
        assert res.status_code == 401

    def test_check_bookmark_endpoint(self, shared_client: TestClient) -> None:
        client = shared_client
        user_id = "bmark_check_user"
        # Add bookmark
        client.post(
            f"/public/blog-posts/{POST_SLUG}/bookmarks",
            headers=_headers(role="user", user_id=user_id),
        )
        # Check via /user/bookmarks/check/{slug}
        res = client.get(
            f"/user/bookmarks/check/{POST_SLUG}",
            headers=_headers(role="user", user_id=user_id),
        )
        assert res.status_code == 200
        assert res.json() is True


# ── Social stats ──


class TestSocialStats:
    def test_returns_counts(self, shared_client: TestClient) -> None:
        client = shared_client
        client.post(
            f"/public/blog-posts/{POST_SLUG}/reactions",
            headers=_headers(role="user", user_id="stat_liker"),
            json={"emoji": "👍"},
        )
        stats = client.get(
            f"/public/blog-posts/{POST_SLUG}/social-stats",
            headers=_headers(role="user", user_id="stat_viewer"),
        ).json()
        assert "reaction_counts" in stats
        assert "comment_count" in stats
        assert isinstance(stats["reaction_counts"], dict)
        assert stats["reaction_counts"].get("👍", 0) >= 1

    def test_requires_auth(self, shared_client: TestClient) -> None:
        """Social stats should require auth."""
        client = shared_client
        res = client.get(f"/public/blog-posts/{POST_SLUG}/social-stats")
        assert res.status_code == 401

    def test_nonexistent_post_returns_404(self, shared_client: TestClient) -> None:
        client = shared_client
        res = client.get(
            "/public/blog-posts/nonexistent-999/social-stats",
            headers=_headers(role="user"),
        )
        assert res.status_code == 404


# ── User reactions endpoint ──


class TestUserReactions:
    def test_endpoint(self, shared_client: TestClient) -> None:
        client = shared_client
        user_id = "reaction_check_user"
        client.post(
            f"/public/blog-posts/{POST_SLUG}/reactions",
            headers=_headers(role="user", user_id=user_id),
            json={"emoji": "👍"},
        )
        res = client.get(
            f"/public/blog-posts/{POST_SLUG}/user-reactions",
            headers=_headers(role="user", user_id=user_id),
        )
        assert res.status_code == 200
        reactions = res.json()
        assert isinstance(reactions, list)
        assert "👍" in reactions

    def test_requires_auth(self, shared_client: TestClient) -> None:
        client = shared_client
        res = client.get(f"/public/blog-posts/{POST_SLUG}/user-reactions")
        assert res.status_code == 401
