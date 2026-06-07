"""Comprehensive tests for SEO analytics module.

Covers the ``_analyze_seo`` helper, ``_publish_month_key`` helper, and
the full ``/admin/seo-analytics/*`` API endpoints through route-level tests.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    sign_admin_identity,
)
from backend.app.blog import BlogPostCreate, BlogRepository
from backend.app.blog_ideas import BlogIdea, BlogIdeaCreate, BlogIdeaRepository
from backend.app.blog_tags import InMemoryBlogTagRepository
from backend.app.main import create_app
from backend.app.seo_analytics import _analyze_seo, _publish_month_key
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


def _make_idea(
    repo: BlogIdeaRepository,
    title: str = "Test Idea",
    marketing_metadata: dict | None = None,
) -> BlogIdea:
    idea = repo.create(
        BlogIdeaCreate(
            title=title, angle="Test", target_reader="Devs", article_goal="Inform"
        )
    )
    if marketing_metadata is not None:
        idea.marketing_metadata = marketing_metadata
        repo._ideas[idea.id] = idea  # type: ignore[attr-defined]
    return idea


# ===========================================================================
# Unit: _analyze_seo
# ===========================================================================


class TestAnalyzeSeo:
    """Direct tests for the _analyze_seo helper function."""

    def test_none_metadata_returns_zero_and_issue(self) -> None:
        result = _analyze_seo(None)
        assert result["score"] == 0
        assert "No marketing metadata" in result["issues"]

    def test_empty_dict_metadata_is_falsy_returns_zero(self) -> None:
        """{} is falsy in Python, so it hits 'if not metadata' and returns score 0."""
        result = _analyze_seo({})
        assert result["score"] == 0
        assert result["issues"] == ["No marketing metadata"]

    def test_metadata_with_only_missing_fields_returns_low_score(self) -> None:
        result = _analyze_seo({"seo_title": None, "meta_description": None})
        # 100 - 30 (missing title) - 25 (missing desc) - 10 (no keywords) = 35
        assert result["score"] == 35
        assert len(result["issues"]) == 3

    def test_seo_title_too_long_deducts_10(self) -> None:
        metadata = {
            "seo_title": "A" * 61,
            "meta_description": "Good description that is long enough for the test.",
            "keywords": ["ai"],
        }
        result = _analyze_seo(metadata)
        # 100 - 10 (too long) = 90
        assert result["score"] == 90
        assert any("too long" in i for i in result["issues"])

    def test_seo_title_too_short_deducts_5(self) -> None:
        metadata = {
            "seo_title": "Short",
            "meta_description": "Good description that is long enough for the test.",
            "keywords": ["ai"],
        }
        result = _analyze_seo(metadata)
        # 100 - 5 (too short) = 95
        assert result["score"] == 95

    def test_missing_meta_description_deducts_25(self) -> None:
        metadata = {
            "seo_title": "Perfect length title here",
            "keywords": ["ai"],
        }
        result = _analyze_seo(metadata)
        # 100 - 25 (missing desc) = 75
        assert result["score"] == 75

    def test_meta_description_too_long_deducts_10(self) -> None:
        metadata = {
            "seo_title": "Good title that is long enough",  # 31 chars, fine
            "meta_description": "D" * 161,
            "keywords": ["ai"],
        }
        result = _analyze_seo(metadata)
        # 100 - 10 (too long desc) = 90
        assert result["score"] == 90
        assert any("too long" in i for i in result["issues"])

    def test_meta_description_too_short_deducts_5(self) -> None:
        metadata = {
            "seo_title": "Good title that is long enough",  # 31 chars, fine
            "meta_description": "Short",
            "keywords": ["ai"],
        }
        result = _analyze_seo(metadata)
        # 100 - 5 (too short desc) = 95
        assert result["score"] == 95
        assert any("too short" in i for i in result["issues"])

    def test_no_keywords_deducts_10(self) -> None:
        metadata = {
            "seo_title": "Good title that is long enough now",  # ~33 chars, fine
            "meta_description": "Good description that is long enough for the test.",
            "keywords": [],
        }
        result = _analyze_seo(metadata)
        # 100 - 10 (no keywords) = 90
        assert result["score"] == 90
        assert any("No keywords" in i for i in result["issues"])

    def test_too_many_keywords_deducts_5(self) -> None:
        metadata = {
            "seo_title": "Good title that is long enough now",  # ~33 chars, fine
            "meta_description": "Good description that is long enough for the test.",
            "keywords": ["a", "b", "c", "d", "e", "f"],
        }
        result = _analyze_seo(metadata)
        # 100 - 5 (too many keywords) = 95
        assert result["score"] == 95
        assert any("Too many keywords" in i for i in result["issues"])

    def test_perfect_seo_returns_100(self) -> None:
        metadata = {
            "seo_title": "Perfect Length SEO Title Here!",  # 30 chars, >20 and <60
            "meta_description": "A well-written meta description that hits the sweet spot perfectly for SEO.",  # ~66 chars, >50 and <160
            "keywords": ["ai", "test"],
        }
        result = _analyze_seo(metadata)
        assert result["score"] == 100
        assert result["issues"] == []
        assert 20 <= result["details"]["seo_title_length"] <= 60
        assert 50 <= result["details"]["meta_description_length"] <= 160
        assert result["details"]["keyword_count"] == 2

    def test_details_includes_counts(self) -> None:
        metadata = {
            "seo_title": "Test",
            "meta_description": "Desc",
            "keywords": ["kw1"],
        }
        result = _analyze_seo(metadata)
        assert result["details"]["seo_title_length"] == 4
        assert result["details"]["meta_description_length"] == 4
        assert result["details"]["keyword_count"] == 1

    def test_non_string_seo_title(self) -> None:
        metadata = {
            "seo_title": 123,  # non-string
            "meta_description": "Good description that is long enough for the test.",
            "keywords": ["ai"],
        }
        result = _analyze_seo(metadata)
        # str(123) = "123" length 3 -> too short -> -5
        assert result["score"] == 95
        assert result["details"]["seo_title_length"] == 3

    def test_keywords_not_a_list(self) -> None:
        """keywords="not_a_list" is a truthy string; not keywords -> False; isinstance -> False -> no deduction."""
        metadata = {
            "seo_title": "Good title that is long enough now",  # ~33 chars, fine
            "meta_description": "Good description that is long enough for the test.",
            "keywords": "not_a_list",
        }
        result = _analyze_seo(metadata)
        # keywords is truthy string, not a list -> no deduction for keywords
        assert result["score"] == 100
        assert result["details"]["keyword_count"] == 0


# ===========================================================================
# Unit: _publish_month_key
# ===========================================================================


class TestPublishMonthKey:
    """Tests for the _publish_month_key helper."""

    def test_none_returns_unknown(self) -> None:
        assert _publish_month_key(None) == "unknown"

    def test_valid_datetime_returns_yyyy_mm(self) -> None:
        dt = datetime(2026, 6, 7, tzinfo=UTC)
        assert _publish_month_key(dt) == "2026-06"

    def test_january_date(self) -> None:
        dt = datetime(2025, 1, 15, tzinfo=UTC)
        assert _publish_month_key(dt) == "2025-01"


# ===========================================================================
# API: /admin/seo-analytics/stats
# ===========================================================================


class TestSeoAnalyticsStatsAPI:
    """Tests for the GET /admin/seo-analytics/stats endpoint."""

    def test_stats_requires_auth(self) -> None:
        settings = _test_settings()
        app = create_app(settings)
        client = TestClient(app)
        response = client.get("/admin/seo-analytics/stats")
        assert response.status_code == 401

    def test_stats_with_ideas_no_marketing_metadata(self) -> None:
        settings = _test_settings()
        ideas_repo = BlogIdeaRepository()
        _make_idea(ideas_repo, title="Idea without metadata", marketing_metadata=None)

        app = create_app(settings, blog_idea_repository=ideas_repo)
        client = TestClient(app)
        response = client.get("/admin/seo-analytics/stats", headers=_admin_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["ideas_with_seo"] == 0
        assert data["avg_seo_score"] == 0.0
        assert data["total_seo_issues"] == 0
        assert data["posts_needing_attention"] == 0

    def test_stats_with_mixed_seo_scores(self) -> None:
        settings = _test_settings()
        ideas_repo = BlogIdeaRepository()

        # Idea with perfect SEO
        _make_idea(ideas_repo, "Perfect SEO", {
            "seo_title": "Perfect title for SEO testing here",
            "meta_description": "Great description that is perfectly long enough for SEO testing here.",
            "keywords": ["ai", "test"],
        })
        # Idea with poor SEO (missing fields)
        _make_idea(ideas_repo, "Poor SEO", {
            "seo_title": None,
            "meta_description": None,
        })

        app = create_app(settings, blog_idea_repository=ideas_repo)
        client = TestClient(app)
        response = client.get("/admin/seo-analytics/stats", headers=_admin_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["ideas_with_seo"] == 2
        # (100 + 35) / 2 = 67.5
        assert data["avg_seo_score"] == 67.5
        assert data["total_seo_issues"] == 3  # perfect: 0, poor: 3
        assert data["posts_needing_attention"] == 1

    def test_stats_with_publish_trend(self) -> None:
        settings = _test_settings()
        blog_repo = BlogRepository()

        # Clear existing posts and create fresh ones
        blog_repo.posts.clear()

        jan_post = blog_repo.create(
            BlogPostCreate(
                slug="jan-post", title="Jan Post", excerpt="Test",
                author_name="Tester", content_markdown="# Jan",
            )
        )
        blog_repo.publish(jan_post.id)
        jan_updated = blog_repo.posts[jan_post.id].model_copy(
            update={"published_at": datetime(2026, 1, 15, tzinfo=UTC)}
        )
        blog_repo.posts[jan_post.id] = jan_updated

        jun_post = blog_repo.create(
            BlogPostCreate(
                slug="jun-post", title="Jun Post", excerpt="Test",
                author_name="Tester", content_markdown="# Jun",
            )
        )
        blog_repo.publish(jun_post.id)
        jun_updated = blog_repo.posts[jun_post.id].model_copy(
            update={"published_at": datetime(2026, 6, 1, tzinfo=UTC)}
        )
        blog_repo.posts[jun_post.id] = jun_updated

        app = create_app(settings, blog_repository=blog_repo)
        client = TestClient(app)
        response = client.get("/admin/seo-analytics/stats", headers=_admin_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["published_posts"] == 2
        assert data["publish_trend"]["2026-01"] == 1
        assert data["publish_trend"]["2026-06"] == 1
        assert data["draft_posts"] == 0

    def test_stats_counts_tags(self) -> None:
        settings = _test_settings()
        tags_repo = InMemoryBlogTagRepository()

        app = create_app(settings, blog_tag_repository=tags_repo)
        client = TestClient(app)
        response = client.get("/admin/seo-analytics/stats", headers=_admin_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["tags"] > 0  # default tags exist


# ===========================================================================
# API: /admin/seo-analytics/posts
# ===========================================================================


class TestSeoAnalyticsPostsAPI:
    """Tests for the GET /admin/seo-analytics/posts endpoint."""

    def test_posts_returns_per_post_seo_analysis(self) -> None:
        settings = _test_settings()
        ideas_repo = BlogIdeaRepository()
        blog_repo = BlogRepository()

        # Create a blog post and link it to an idea
        post = blog_repo.create(
            BlogPostCreate(
                slug="seo-post", title="SEO Post", excerpt="Test",
                author_name="Tester", content_markdown="# SEO",
            )
        )
        idea = _make_idea(ideas_repo, "SEO Idea", {
            "seo_title": "SEO Title", "meta_description": "Good meta description here.",
            "keywords": ["seo"],
        })
        idea.published_blog_post_id = post.id
        ideas_repo._ideas[idea.id] = idea  # type: ignore[attr-defined]

        app = create_app(settings, blog_repository=blog_repo, blog_idea_repository=ideas_repo)
        client = TestClient(app)
        response = client.get("/admin/seo-analytics/posts", headers=_admin_headers())
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # At least our post should be there
        assert any(p["post_id"] == post.id for p in data)

    def test_posts_with_min_score_filter(self) -> None:
        settings = _test_settings()
        ideas_repo = BlogIdeaRepository()
        blog_repo = BlogRepository()

        # Post with no marketing metadata (score 0)
        post = blog_repo.create(
            BlogPostCreate(
                slug="no-seo-post", title="No SEO", excerpt="Test",
                author_name="Tester", content_markdown="# No",
            )
        )

        app = create_app(settings, blog_repository=blog_repo, blog_idea_repository=ideas_repo)
        client = TestClient(app)

        # Filter to only posts with score < 50
        response = client.get(
            "/admin/seo-analytics/posts?min_score=50",
            headers=_admin_headers(),
        )
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["seo_score"] < 50

    def test_posts_sorted_by_seo_score_ascending(self) -> None:
        settings = _test_settings()
        ideas_repo = BlogIdeaRepository()
        blog_repo = BlogRepository()

        post1 = blog_repo.create(
            BlogPostCreate(
                slug="first", title="First", excerpt="T", author_name="T",
                content_markdown="# 1",
            )
        )
        idea1 = _make_idea(ideas_repo, "Idea 1", {
            "seo_title": "Perfect length for sure", "meta_description": "Good desc here.",
            "keywords": ["a"],
        })
        idea1.published_blog_post_id = post1.id
        ideas_repo._ideas[idea1.id] = idea1  # type: ignore[attr-defined]

        app = create_app(settings, blog_repository=blog_repo, blog_idea_repository=ideas_repo)
        client = TestClient(app)
        response = client.get("/admin/seo-analytics/posts", headers=_admin_headers())
        assert response.status_code == 200
        data = response.json()
        scores = [p["seo_score"] for p in data]
        assert scores == sorted(scores)

    def test_posts_has_marketing_metadata_flag(self) -> None:
        settings = _test_settings()
        ideas_repo = BlogIdeaRepository()
        blog_repo = BlogRepository()

        post = blog_repo.create(
            BlogPostCreate(
                slug="meta-post", title="Meta Post", excerpt="T",
                author_name="T", content_markdown="# M",
            )
        )
        idea = _make_idea(ideas_repo, "Meta Idea", {
            "seo_title": "Title", "meta_description": "Desc", "keywords": ["k"],
        })
        idea.published_blog_post_id = post.id
        ideas_repo._ideas[idea.id] = idea  # type: ignore[attr-defined]

        app = create_app(settings, blog_repository=blog_repo, blog_idea_repository=ideas_repo)
        client = TestClient(app)
        response = client.get("/admin/seo-analytics/posts", headers=_admin_headers())
        data = response.json()
        meta_post = next(p for p in data if p["post_id"] == post.id)
        assert meta_post["has_marketing_metadata"] is True


# ===========================================================================
# API: /admin/seo-analytics/keywords
# ===========================================================================


class TestSeoAnalyticsKeywordsAPI:
    """Tests for the GET /admin/seo-analytics/keywords endpoint."""

    def test_keywords_returns_list(self) -> None:
        settings = _test_settings()
        app = create_app(settings)
        client = TestClient(app)
        response = client.get("/admin/seo-analytics/keywords", headers=_admin_headers())
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_keywords_includes_tags_and_marketing_keywords(self) -> None:
        settings = _test_settings()
        ideas_repo = BlogIdeaRepository()

        # Create an idea with marketing keywords
        _make_idea(ideas_repo, "KW Idea", {
            "seo_title": "Title", "meta_description": "Desc",
            "keywords": ["machine-learning", "ai", "ML"],
        })

        tags_repo = InMemoryBlogTagRepository()
        app = create_app(
            settings,
            blog_idea_repository=ideas_repo,
            blog_tag_repository=tags_repo,
        )
        client = TestClient(app)
        response = client.get("/admin/seo-analytics/keywords", headers=_admin_headers())
        assert response.status_code == 200
        data = response.json()
        # Should contain "ai" (lowercased), "machine-learning", "ml" keywords
        keyword_items = [kw for kw in data if kw["type"] == "keyword"]
        assert len(keyword_items) >= 2
        names = [kw["name"] for kw in keyword_items]
        assert "ai" in names
        assert "machine-learning" in names
        assert "ml" in names

    def test_keywords_case_insensitive_grouping(self) -> None:
        ideas_repo = BlogIdeaRepository()
        _make_idea(ideas_repo, "Idea 1", {
            "seo_title": "T", "meta_description": "D",
            "keywords": ["AI", "Machine-Learning"],
        })
        _make_idea(ideas_repo, "Idea 2", {
            "seo_title": "T", "meta_description": "D",
            "keywords": ["ai", "machine-learning"],
        })

        settings = _test_settings()
        app = create_app(settings, blog_idea_repository=ideas_repo)
        client = TestClient(app)
        response = client.get("/admin/seo-analytics/keywords", headers=_admin_headers())
        data = response.json()
        ai_kws = [kw for kw in data if kw["name"] == "ai"]
        assert len(ai_kws) == 1
        assert ai_kws[0]["count"] == 2

    def test_keywords_respects_limit_50(self) -> None:
        ideas_repo = BlogIdeaRepository()
        many_keywords = [f"kw-{i}" for i in range(60)]
        _make_idea(ideas_repo, "Many KWs", {
            "seo_title": "T", "meta_description": "D",
            "keywords": many_keywords,
        })

        settings = _test_settings()
        app = create_app(settings, blog_idea_repository=ideas_repo)
        client = TestClient(app)
        response = client.get("/admin/seo-analytics/keywords", headers=_admin_headers())
        data = response.json()
        assert len(data) <= 50
