"""Tests for publish-from-approved-idea bridge (US-032)."""

import json
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    sign_admin_identity,
)
from backend.app.blog import BlogPostCreate, BlogRepository
from backend.app.blog_ideas import (
    BlogIdeaCreate,
    BlogIdeaRepository,
    BlogIdeaUpdate,
    OutlineSection,
)
from backend.app.blog_publish import (
    build_blog_post_create,
    publish_idea_to_blog,
    slugify_title,
    unique_slug,
    validate_idea_ready_to_publish,
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


def _marketing_metadata() -> dict:
    return {
        "seo_title": "AI Lab Publish Bridge",
        "meta_description": "How we ship grounded AI blog posts with human review.",
        "canonical_url": "https://example.com/blog/ai-lab-publish-bridge",
        "social_headline": "Publish bridge",
        "social_description": "From approved idea to live post.",
        "cta_text": "Read more",
        "tags": ["ai", "cms"],
    }


def _ready_idea(repo: BlogIdeaRepository):
    idea = repo.create(
        BlogIdeaCreate(
            title="Publish Bridge Idea",
            angle="Product",
            target_reader="Admins",
            article_goal="Explain the bridge",
        )
    )
    repo.update(idea.id, BlogIdeaUpdate(status="approved"))
    repo.set_outline(
        idea.id,
        [OutlineSection(section="Intro", points=["Hook"])],
        status="approved",
    )
    repo.set_draft(idea.id, "# Publish Bridge\n\nBody copy.", status="approved")
    repo.set_technical_review(
        idea.id,
        {
            "overall_risk": "low",
            "issues": [],
            "approval_recommendation": "approve",
        },
        status="approved",
    )
    repo.set_marketing_metadata(idea.id, _marketing_metadata(), status="approved")
    linked = repo.get_by_id(idea.id)
    assert linked is not None
    return linked


class TestBlogPublishHelpers:
    def test_slugify_title(self) -> None:
        assert slugify_title("Hello World!") == "hello-world"

    def test_unique_slug_avoids_collision(self) -> None:
        blog_repo = BlogRepository(posts=[])
        assert unique_slug("hello-world", blog_repo) == "hello-world"
        blog_repo.create(
            BlogPostCreate(
                slug="hello-world",
                title="Existing",
                excerpt="Taken slug",
                author_name="AI Lab Team",
                content_markdown="Existing post.",
            )
        )
        assert unique_slug("hello-world", blog_repo) == "hello-world-2"

    def test_validate_requires_approved_stages(self) -> None:
        repo = BlogIdeaRepository()
        idea = repo.create(
            BlogIdeaCreate(
                title="Incomplete",
                angle="Test",
                target_reader="Devs",
                article_goal="Test",
            )
        )
        with pytest.raises(HTTPException) as exc:
            validate_idea_ready_to_publish(idea)
        assert exc.value.status_code == 400


class TestPublishIdeaToBlog:
    def test_publish_creates_and_links_post(self) -> None:
        ideas_repo = BlogIdeaRepository()
        blog_repo = BlogRepository(posts=[])
        idea = _ready_idea(ideas_repo)

        post_id, slug, already = publish_idea_to_blog(idea.id, ideas_repo, blog_repo)

        assert already is False
        assert slug == "ai-lab-publish-bridge"
        post = blog_repo.get_by_id(post_id)
        assert post is not None
        assert post.status == "published"
        assert post.content_markdown.startswith("# Publish Bridge")
        updated = ideas_repo.get_by_id(idea.id)
        assert updated is not None
        assert updated.published_blog_post_id == post_id

    def test_publish_is_idempotent_when_already_linked(self) -> None:
        ideas_repo = BlogIdeaRepository()
        blog_repo = BlogRepository(posts=[])
        idea = _ready_idea(ideas_repo)
        first_id, first_slug, _ = publish_idea_to_blog(idea.id, ideas_repo, blog_repo)
        second_id, second_slug, already = publish_idea_to_blog(idea.id, ideas_repo, blog_repo)
        assert already is True
        assert second_id == first_id
        assert second_slug == first_slug
        assert len(blog_repo.list_all()) == 1


class TestPublishToBlogRoute:
    def test_publish_to_blog_via_api(self) -> None:
        ideas_repo = BlogIdeaRepository()
        blog_repo = BlogRepository(posts=[])
        idea = _ready_idea(ideas_repo)
        app = create_app(
            settings=_test_settings(),
            blog_repository=blog_repo,
            blog_idea_repository=ideas_repo,
        )
        client = TestClient(app)

        response = client.post(
            f"/admin/blog-ideas/{idea.id}/publish-to-blog",
            headers=_admin_headers(),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["slug"] == "ai-lab-publish-bridge"
        assert body["already_linked"] is False
        public = client.get("/public/blog-posts")
        assert response.status_code == 200
        slugs = {item["slug"] for item in public.json()}
        assert "ai-lab-publish-bridge" in slugs

    def test_publish_to_blog_rejects_incomplete_idea(self) -> None:
        ideas_repo = BlogIdeaRepository()
        blog_repo = BlogRepository(posts=[])
        idea = ideas_repo.create(
            BlogIdeaCreate(
                title="Incomplete",
                angle="Test",
                target_reader="Devs",
                article_goal="Test",
            )
        )
        app = create_app(
            settings=_test_settings(),
            blog_repository=blog_repo,
            blog_idea_repository=ideas_repo,
        )
        client = TestClient(app)
        response = client.post(
            f"/admin/blog-ideas/{idea.id}/publish-to-blog",
            headers=_admin_headers(),
        )
        assert response.status_code == 400
