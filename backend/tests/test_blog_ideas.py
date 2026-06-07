"""Comprehensive tests for the blog_ideas module.

Tests cover:
- Pydantic model creation and validation
- ``marketing_metadata_for_storage`` helper
- ``BlogIdeaRepository`` (InMemory) CRUD and workflow methods
- Route handlers via ``FastAPI TestClient`` with mocked dependencies
- The ``run-next`` state machine decision tree
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from pydantic import ValidationError

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    AdminIdentity,
)
from backend.app.blog_ideas import (
    BlogIdea,
    BlogIdeaCreate,
    BlogIdeaRepository,
    BlogIdeaSummary,
    BlogIdeaUpdate,
    OutlineSection,
    PublishFromIdeaResponse,
    create_blog_idea_routes,
    marketing_metadata_for_storage,
)
from backend.app.llm.schemas import MarketingMetadata
from backend.app.settings import Settings

# =========================================================================
# Constants
# =========================================================================

TEST_SECRET = "test-secret-at-least-32-characters-long!!"

# =========================================================================
# Helpers
# =========================================================================


def _make_idea(**overrides: object) -> BlogIdea:
    """Construct a ``BlogIdea`` with sensible defaults."""
    now = datetime.now(UTC)
    return BlogIdea(
        id=str(overrides.get("id", "idea_test_001")),
        title=str(overrides.get("title", "Test Blog Idea")),
        angle=str(overrides.get("angle", "AI Testing")),
        target_reader=str(overrides.get("target_reader", "Developers")),
        article_goal=str(overrides.get("article_goal", "Show testing approach")),
        positioning_notes=list(overrides.get("positioning_notes", [])),
        source=str(overrides.get("source", "manual")),
        status=str(overrides.get("status", "pending")),
        reviewed_by=overrides.get("reviewed_by"),
        reviewed_at=overrides.get("reviewed_at"),
        feedback=overrides.get("feedback"),
        outline_sections=list(overrides.get("outline_sections", [])),
        outline_status=overrides.get("outline_status"),
        draft_markdown=overrides.get("draft_markdown"),
        draft_status=overrides.get("draft_status"),
        technical_review=overrides.get("technical_review"),
        technical_review_status=overrides.get("technical_review_status"),
        marketing_metadata=overrides.get("marketing_metadata"),
        marketing_status=overrides.get("marketing_status"),
        published_blog_post_id=overrides.get("published_blog_post_id"),
        created_at=overrides.get("created_at", now),  # type: ignore[arg-type]
        updated_at=overrides.get("updated_at", now),  # type: ignore[arg-type]
    )


def _create_payload(**overrides: object) -> dict[str, object]:
    return {
        "title": str(overrides.get("title", "New Blog Idea")),
        "angle": str(overrides.get("angle", "AI Testing")),
        "target_reader": str(overrides.get("target_reader", "Developers")),
        "article_goal": str(overrides.get("article_goal", "Show testing")),
        "positioning_notes": list(overrides.get("positioning_notes", [])),
    }


def _admin_headers() -> dict[str, str]:
    """Create signed admin identity headers for test requests."""
    now = int(time.time())
    payload = json.dumps(
        {
            "user_id": "admin_1",
            "email": "admin@test.com",
            "role": "admin",
            "issued_at": now,
        },
        separators=(",", ":"),
    )
    sig = hmac.new(
        TEST_SECRET.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    return {
        ADMIN_IDENTITY_HEADER: payload,
        ADMIN_SIGNATURE_HEADER: sig,
    }


# =========================================================================
# Pydantic Model Tests
# =========================================================================


class TestBlogIdeaModel:
    """Verify ``BlogIdea`` construction, defaults, and field types."""

    def test_creation_with_all_fields(self) -> None:
        now = datetime.now(UTC)
        idea = BlogIdea(
            id="idea_1",
            title="How to Test AI in Production",
            angle="Testing strategies",
            target_reader="ML Engineers",
            article_goal="Share testing best practices",
            positioning_notes=["Assume limited GPU access"],
            source="ai_generated",
            status="approved",
            reviewed_by="admin_1",
            reviewed_at=now,
            feedback="Great idea",
            outline_sections=[OutlineSection(section="Intro", points=["P1"])],
            outline_status="approved",
            draft_markdown="# Full draft",
            draft_status="pending",
            technical_review={"risk": "low"},
            technical_review_status="approved",
            marketing_metadata={"seo_title": "SEO"},
            marketing_status="pending",
            published_blog_post_id="post_abc",
            scheduled_at=now,
            created_at=now,
            updated_at=now,
        )
        assert idea.id == "idea_1"
        assert idea.title == "How to Test AI in Production"
        assert idea.status == "approved"
        assert idea.source == "ai_generated"
        assert idea.reviewed_by == "admin_1"
        assert idea.outline_status == "approved"
        assert idea.draft_markdown == "# Full draft"
        assert idea.technical_review == {"risk": "low"}
        assert idea.marketing_metadata == {"seo_title": "SEO"}
        assert idea.published_blog_post_id == "post_abc"
        assert idea.scheduled_at is not None

    def test_defaults(self) -> None:
        now = datetime.now(UTC)
        idea = BlogIdea(
            id="idea_2",
            title="Test",
            angle="A",
            target_reader="D",
            article_goal="G",
            created_at=now,
            updated_at=now,
        )
        assert idea.status == "pending"
        assert idea.source == "manual"
        assert idea.positioning_notes == []
        assert idea.outline_sections == []
        assert idea.outline_status is None
        assert idea.draft_status is None
        assert idea.technical_review is None
        assert idea.marketing_status is None
        assert idea.published_blog_post_id is None
        assert idea.reviewed_by is None
        assert idea.reviewed_at is None
        assert idea.feedback is None

    def test_source_literal_cases(self) -> None:
        now = datetime.now(UTC)
        manual = BlogIdea(
            id="m", title="M", angle="A", target_reader="D",
            article_goal="G", source="manual", created_at=now, updated_at=now,
        )
        ai = BlogIdea(
            id="a", title="A", angle="A", target_reader="D",
            article_goal="G", source="ai_generated", created_at=now, updated_at=now,
        )
        assert manual.source == "manual"
        assert ai.source == "ai_generated"


class TestBlogIdeaCreate:
    """Validate the creation payload model."""

    def test_valid_payload(self) -> None:
        payload = BlogIdeaCreate(
            title="Valid Title",
            angle="An angle",
            target_reader="Developers",
            article_goal="Inform",
        )
        assert payload.title == "Valid Title"
        assert payload.positioning_notes == []

    def test_title_min_length(self) -> None:
        with pytest.raises(ValidationError):
            BlogIdeaCreate(
                title="", angle="A", target_reader="D", article_goal="G"
            )

    def test_title_max_length(self) -> None:
        with pytest.raises(ValidationError):
            BlogIdeaCreate(
                title="x" * 241, angle="A", target_reader="D", article_goal="G"
            )

    def test_angle_max_length(self) -> None:
        with pytest.raises(ValidationError):
            BlogIdeaCreate(
                title="Title", angle="x" * 161,
                target_reader="D", article_goal="G",
            )

    def test_target_reader_max_length(self) -> None:
        with pytest.raises(ValidationError):
            BlogIdeaCreate(
                title="Title", angle="A",
                target_reader="x" * 161, article_goal="G",
            )

    def test_article_goal_min_length(self) -> None:
        with pytest.raises(ValidationError):
            BlogIdeaCreate(
                title="Title", angle="A", target_reader="D", article_goal="",
            )


class TestBlogIdeaSummary:
    """Lightweight list view model."""

    def test_construction(self) -> None:
        now = datetime.now(UTC)
        summary = BlogIdeaSummary(
            id="idea_1",
            title="Summary Test",
            angle="Angle",
            source="manual",
            status="approved",
            outline_status=None,
            draft_status="pending",
            technical_review_status=None,
            marketing_status=None,
            created_at=now,
        )
        assert summary.id == "idea_1"
        assert summary.title == "Summary Test"
        assert summary.source == "manual"
        assert summary.status == "approved"
        assert summary.outline_status is None
        assert summary.draft_status == "pending"


class TestOutlineSection:
    """Section within an outline."""

    def test_creation(self) -> None:
        section = OutlineSection(
            section="Introduction",
            points=["Context", "Problem statement", "Goals"],
        )
        assert section.section == "Introduction"
        assert len(section.points) == 3

    def test_empty_points(self) -> None:
        section = OutlineSection(section="Empty", points=[])
        assert section.points == []


class TestPublishFromIdeaResponse:
    """Publish bridge result model."""

    def test_defaults(self) -> None:
        resp = PublishFromIdeaResponse(
            blog_post_id="post_42", slug="test-post"
        )
        assert resp.blog_post_id == "post_42"
        assert resp.slug == "test-post"
        assert resp.already_linked is False

    def test_already_linked_true(self) -> None:
        resp = PublishFromIdeaResponse(
            blog_post_id="post_42", slug="test-post", already_linked=True
        )
        assert resp.already_linked is True


# =========================================================================
# Helper Function Tests
# =========================================================================


class TestMarketingMetadataForStorage:
    """Normalize LLM marketing output to storage format."""

    def test_normal_conversion(self) -> None:
        mm = MarketingMetadata(
            seo_title="SEO Title for the Post",
            meta_description="A concise meta description.",
            excerpt="Display excerpt.",
            linkedin_post="LinkedIn share text.",
            x_post="X/Twitter share text.",
            cta="Contact us now.",
        )
        result = marketing_metadata_for_storage(mm)
        assert result["seo_title"] == "SEO Title for the Post"
        assert result["meta_description"] == "A concise meta description."
        assert result["excerpt"] == "Display excerpt."
        assert result["social_headline"] == "LinkedIn share text."
        assert result["social_description"] == "X/Twitter share text."
        assert result["cta_text"] == "Contact us now."
        assert result["canonical_url"] == ""
        assert result["tags"] == []

    def test_excerpt_falls_back_to_meta_description(self) -> None:
        mm = MarketingMetadata(
            seo_title="SEO",
            meta_description="Fallback description.",
            excerpt="",
            linkedin_post="LI",
            x_post="X",
            cta="CTA",
        )
        result = marketing_metadata_for_storage(mm)
        assert result["excerpt"] == "Fallback description."

    def test_excerpt_strips_whitespace(self) -> None:
        mm = MarketingMetadata(
            seo_title="SEO",
            meta_description="Desc.",
            excerpt="  Extra whitespace  ",
            linkedin_post="LI",
            x_post="X",
            cta="CTA",
        )
        result = marketing_metadata_for_storage(mm)
        # .strip() removes leading/trailing whitespace including the trailing period
        assert result["excerpt"] == "Extra whitespace"

    def test_excerpt_uses_meta_description_when_excerpt_empty(self) -> None:
        mm = MarketingMetadata(
            seo_title="SEO",
            meta_description="  Spaced meta desc.  ",
            excerpt="",
            linkedin_post="LI",
            x_post="X",
            cta="CTA",
        )
        result = marketing_metadata_for_storage(mm)
        assert result["excerpt"] == "Spaced meta desc."


# =========================================================================
# BlogIdeaRepository (InMemory) Tests
# =========================================================================


class TestBlogIdeaRepository:
    """Full CRUD and workflow coverage for the in-memory repository."""

    def test_empty_repo_returns_empty_list(self) -> None:
        repo = BlogIdeaRepository()
        assert repo.list_all() == []

    def test_create_returns_populated_idea(self) -> None:
        repo = BlogIdeaRepository()
        payload = BlogIdeaCreate(
            title="Test Idea",
            angle="AI Testing",
            target_reader="Developers",
            article_goal="Show testing approaches",
            positioning_notes=["Note 1"],
        )
        idea = repo.create(payload)
        assert idea.id.startswith("idea_")
        assert idea.title == "Test Idea"
        assert idea.angle == "AI Testing"
        assert idea.source == "manual"
        assert idea.status == "pending"
        assert idea.positioning_notes == ["Note 1"]
        assert idea.created_at is not None

    def test_create_and_retrieve_by_id(self) -> None:
        repo = BlogIdeaRepository()
        created = repo.create(
            BlogIdeaCreate(
                title="Find Me", angle="A", target_reader="D", article_goal="G"
            )
        )
        fetched = repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.title == "Find Me"
        assert fetched.id == created.id

    def test_get_by_id_returns_none_for_missing(self) -> None:
        repo = BlogIdeaRepository()
        assert repo.get_by_id("nonexistent") is None

    def test_add_generated_sets_source_and_context(self) -> None:
        repo = BlogIdeaRepository()
        payload = BlogIdeaCreate(
            title="AI Gen", angle="A", target_reader="D", article_goal="G"
        )
        context = {"project_name": "Test Project", "summary": "A test"}
        idea = repo.add_generated(payload, context=context)
        assert idea.source == "ai_generated"
        assert idea.source_project_context == context
        assert idea.id.startswith("idea_")

    def test_add_generated_without_context(self) -> None:
        repo = BlogIdeaRepository()
        payload = BlogIdeaCreate(
            title="AI Gen", angle="A", target_reader="D", article_goal="G"
        )
        idea = repo.add_generated(payload)
        assert idea.source == "ai_generated"
        assert idea.source_project_context is None

    def test_list_all_sorted_descending(self) -> None:
        repo = BlogIdeaRepository()
        first = repo.create(
            BlogIdeaCreate(
                title="First", angle="A", target_reader="D", article_goal="G"
            )
        )
        # Small sleep so second idea has a distinctly later timestamp
        time.sleep(0.01)
        second = repo.create(
            BlogIdeaCreate(
                title="Second", angle="B", target_reader="D", article_goal="G"
            )
        )
        all_ideas = repo.list_all()
        assert len(all_ideas) == 2
        # Most recent (second) first
        assert all_ideas[0].title == "Second"
        assert all_ideas[1].title == "First"

    def test_update_approve_sets_review_metadata(self) -> None:
        repo = BlogIdeaRepository()
        idea = repo.create(
            BlogIdeaCreate(
                title="Approve Me", angle="A", target_reader="D", article_goal="G"
            )
        )
        updated = repo.update(idea.id, BlogIdeaUpdate(status="approved"))
        assert updated is not None
        assert updated.status == "approved"
        assert updated.reviewed_by == "admin"
        assert updated.reviewed_at is not None
        assert updated.updated_at is not None

    def test_update_reject_sets_review_metadata(self) -> None:
        repo = BlogIdeaRepository()
        idea = repo.create(
            BlogIdeaCreate(
                title="Reject Me", angle="A", target_reader="D", article_goal="G"
            )
        )
        updated = repo.update(idea.id, BlogIdeaUpdate(status="rejected"))
        assert updated is not None
        assert updated.status == "rejected"
        assert updated.reviewed_by == "admin"
        assert updated.reviewed_at is not None

    def test_update_with_feedback(self) -> None:
        repo = BlogIdeaRepository()
        idea = repo.create(
            BlogIdeaCreate(
                title="Feedback", angle="A", target_reader="D", article_goal="G"
            )
        )
        updated = repo.update(
            idea.id, BlogIdeaUpdate(feedback="Needs more data")
        )
        assert updated is not None
        assert updated.feedback == "Needs more data"

    def test_update_nonexistent_returns_none(self) -> None:
        repo = BlogIdeaRepository()
        assert repo.update("missing", BlogIdeaUpdate(status="approved")) is None

    def test_update_outline_status(self) -> None:
        repo = BlogIdeaRepository()
        idea = repo.create(
            BlogIdeaCreate(
                title="Outline St", angle="A", target_reader="D", article_goal="G"
            )
        )
        updated = repo.update(idea.id, BlogIdeaUpdate(outline_status="approved"))
        assert updated is not None
        assert updated.outline_status == "approved"

    def test_update_draft_status(self) -> None:
        repo = BlogIdeaRepository()
        idea = repo.create(
            BlogIdeaCreate(
                title="Draft St", angle="A", target_reader="D", article_goal="G"
            )
        )
        updated = repo.update(idea.id, BlogIdeaUpdate(draft_status="approved"))
        assert updated is not None
        assert updated.draft_status == "approved"

    def test_update_technical_review_status(self) -> None:
        repo = BlogIdeaRepository()
        idea = repo.create(
            BlogIdeaCreate(
                title="Tech St", angle="A", target_reader="D", article_goal="G"
            )
        )
        updated = repo.update(
            idea.id, BlogIdeaUpdate(technical_review_status="approved")
        )
        assert updated is not None
        assert updated.technical_review_status == "approved"

    def test_update_marketing_status(self) -> None:
        repo = BlogIdeaRepository()
        idea = repo.create(
            BlogIdeaCreate(
                title="Mkt St", angle="A", target_reader="D", article_goal="G"
            )
        )
        updated = repo.update(
            idea.id, BlogIdeaUpdate(marketing_status="approved")
        )
        assert updated is not None
        assert updated.marketing_status == "approved"

    def test_update_scheduled_at(self) -> None:
        repo = BlogIdeaRepository()
        idea = repo.create(
            BlogIdeaCreate(
                title="Schedule", angle="A", target_reader="D", article_goal="G"
            )
        )
        future = datetime(2026, 12, 1, tzinfo=UTC)
        updated = repo.update(
            idea.id, BlogIdeaUpdate(scheduled_at=future)
        )
        assert updated is not None
        assert updated.scheduled_at == future

    def test_set_outline(self) -> None:
        repo = BlogIdeaRepository()
        idea = repo.create(
            BlogIdeaCreate(
                title="Outline", angle="A", target_reader="D", article_goal="G"
            )
        )
        sections = [OutlineSection(section="Intro", points=["P1"])]
        result = repo.set_outline(idea.id, sections, status="pending")
        assert result is not None
        assert len(result.outline_sections) == 1
        assert result.outline_sections[0].section == "Intro"
        assert result.outline_status == "pending"
        assert result.updated_at is not None

    def test_set_outline_nonexistent_returns_none(self) -> None:
        repo = BlogIdeaRepository()
        assert repo.set_outline("missing", []) is None

    def test_set_draft(self) -> None:
        repo = BlogIdeaRepository()
        idea = repo.create(
            BlogIdeaCreate(
                title="Draft", angle="A", target_reader="D", article_goal="G"
            )
        )
        result = repo.set_draft(idea.id, "# Markdown content", status="pending")
        assert result is not None
        assert result.draft_markdown == "# Markdown content"
        assert result.draft_status == "pending"

    def test_set_draft_nonexistent_returns_none(self) -> None:
        repo = BlogIdeaRepository()
        assert repo.set_draft("missing", "# Draft") is None

    def test_set_technical_review(self) -> None:
        repo = BlogIdeaRepository()
        idea = repo.create(
            BlogIdeaCreate(
                title="Review", angle="A", target_reader="D", article_goal="G"
            )
        )
        review = {"overall_risk": "low", "issues": []}
        result = repo.set_technical_review(
            idea.id, review, status="pending"
        )
        assert result is not None
        assert result.technical_review == review
        assert result.technical_review_status == "pending"

    def test_set_technical_review_nonexistent(self) -> None:
        repo = BlogIdeaRepository()
        assert repo.set_technical_review("missing", {}) is None

    def test_set_marketing_metadata(self) -> None:
        repo = BlogIdeaRepository()
        idea = repo.create(
            BlogIdeaCreate(
                title="Mkt", angle="A", target_reader="D", article_goal="G"
            )
        )
        meta = {"seo_title": "SEO", "meta_description": "Desc"}
        result = repo.set_marketing_metadata(
            idea.id, meta, status="pending"
        )
        assert result is not None
        assert result.marketing_metadata == meta
        assert result.marketing_status == "pending"

    def test_set_marketing_nonexistent(self) -> None:
        repo = BlogIdeaRepository()
        assert repo.set_marketing_metadata("missing", {}) is None

    def test_link_published_post(self) -> None:
        repo = BlogIdeaRepository()
        idea = repo.create(
            BlogIdeaCreate(
                title="Link", angle="A", target_reader="D", article_goal="G"
            )
        )
        result = repo.link_published_post(idea.id, "post_linked")
        assert result is not None
        assert result.published_blog_post_id == "post_linked"

    def test_link_published_post_nonexistent(self) -> None:
        repo = BlogIdeaRepository()
        assert repo.link_published_post("missing", "post_x") is None

    def test_list_all_returns_summary_type(self) -> None:
        repo = BlogIdeaRepository()
        repo.create(
            BlogIdeaCreate(
                title="List", angle="A", target_reader="D", article_goal="G"
            )
        )
        items = repo.list_all()
        assert len(items) == 1
        assert isinstance(items[0], BlogIdeaSummary)

    def test_repo_initialized_with_ideas(self) -> None:
        now = datetime.now(UTC)
        existing = [
            BlogIdea(
                id="pre_1", title="Pre-existing", angle="A",
                target_reader="D", article_goal="G",
                created_at=now, updated_at=now,
            )
        ]
        repo = BlogIdeaRepository(ideas=existing)
        assert repo.get_by_id("pre_1") is not None
        assert len(repo.list_all()) == 1

    def test_model_copy_on_update(self) -> None:
        """Verify update mutates the stored reference (new object)."""
        repo = BlogIdeaRepository()
        idea = repo.create(
            BlogIdeaCreate(
                title="Original", angle="A", target_reader="D", article_goal="G"
            )
        )
        repo.update(idea.id, BlogIdeaUpdate(status="approved"))
        # The stored reference should differ (new object from model_copy)
        assert repo._ideas[idea.id].status == "approved"

    def test_set_outline_with_custom_status(self) -> None:
        repo = BlogIdeaRepository()
        idea = repo.create(
            BlogIdeaCreate(
                title="Outline Status", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        sections = [OutlineSection(section="Body", points=["P1"])]
        result = repo.set_outline(idea.id, sections, status="approved")
        assert result is not None
        assert result.outline_status == "approved"


# =========================================================================
# App / Route Fixtures
# =========================================================================


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        environment="test",
        admin_boundary_secret=TEST_SECRET,
        llm_e2e_fake=True,
    )


@pytest.fixture
def test_repo() -> BlogIdeaRepository:
    return BlogIdeaRepository()


def _build_test_app(
    repo: BlogIdeaRepository,
    settings: Settings,
    blog_repo: object = None,
    claims_repo: object = None,
    jobs_repo: object = None,
    ai_runs_repo: object = None,
) -> FastAPI:
    """Build a FastAPI app with blog-idea routes and auth bypass.

    Accepts optional repositories for downstream dependencies.
    """
    router = create_blog_idea_routes(
        repository=repo,
        settings=settings,
        blog_repository=blog_repo,
        claims_repository=claims_repo,
        jobs_repository=jobs_repo,
        ai_runs_repository=ai_runs_repo,
    )
    app = FastAPI()
    app.include_router(router)

    async def _fake_admin() -> AdminIdentity:
        return AdminIdentity(
            user_id="admin_1", email="admin@test.com", role="admin"
        )

    # Override the auth dependency so tests don't need real auth
    app.dependency_overrides = {}
    return app


@pytest.fixture
def test_app(
    test_repo: BlogIdeaRepository, test_settings: Settings
) -> FastAPI:
    return _build_test_app(repo=test_repo, settings=test_settings)


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


@pytest_asyncio.fixture
async def async_client(
    test_app: FastAPI,
) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# =========================================================================
# Route Tests — CRUD
# =========================================================================


class TestListIdeas:
    """GET /admin/blog-ideas"""

    def test_empty(self, client: TestClient) -> None:
        resp = client.get("/admin/blog-ideas", headers=_admin_headers())
        assert resp.status_code == 200
        assert resp.json() == []

    def test_with_data(
        self, client: TestClient, test_repo: BlogIdeaRepository
    ) -> None:
        test_repo.create(
            BlogIdeaCreate(
                title="First", angle="A", target_reader="D", article_goal="G"
            )
        )
        test_repo.create(
            BlogIdeaCreate(
                title="Second", angle="B", target_reader="D", article_goal="G"
            )
        )
        resp = client.get("/admin/blog-ideas", headers=_admin_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        titles = {d["title"] for d in data}
        assert titles == {"First", "Second"}

    def test_requires_auth(self, client: TestClient) -> None:
        resp = client.get("/admin/blog-ideas")
        assert resp.status_code == 401

    def test_return_type_is_summary(
        self, client: TestClient, test_repo: BlogIdeaRepository
    ) -> None:
        test_repo.create(
            BlogIdeaCreate(
                title="T", angle="A", target_reader="D", article_goal="G"
            )
        )
        resp = client.get("/admin/blog-ideas", headers=_admin_headers())
        data = resp.json()
        assert "outline_status" in data[0]
        assert "created_at" in data[0]
        # BlogIdeaSummary should not include article_goal
        assert "article_goal" not in data[0]


class TestGetIdea:
    """GET /admin/blog-ideas/{idea_id}"""

    def test_found(
        self, client: TestClient, test_repo: BlogIdeaRepository
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Get Me", angle="A", target_reader="D", article_goal="G"
            )
        )
        resp = client.get(
            f"/admin/blog-ideas/{idea.id}", headers=_admin_headers()
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Get Me"
        assert resp.json()["id"] == idea.id

    def test_not_found(self, client: TestClient) -> None:
        resp = client.get(
            "/admin/blog-ideas/nonexistent", headers=_admin_headers()
        )
        assert resp.status_code == 404
        assert "not found" in resp.text.lower()

    def test_requires_auth(self, client: TestClient) -> None:
        resp = client.get("/admin/blog-ideas/idea_1")
        assert resp.status_code == 401


class TestCreateIdea:
    """POST /admin/blog-ideas"""

    def test_basic(self, client: TestClient) -> None:
        resp = client.post(
            "/admin/blog-ideas",
            headers=_admin_headers(),
            json=_create_payload(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "New Blog Idea"
        assert data["source"] == "manual"
        assert data["status"] == "pending"
        assert data["id"].startswith("idea_")

    def test_with_positioning_notes(self, client: TestClient) -> None:
        payload = _create_payload(positioning_notes=["Note 1", "Note 2"])
        resp = client.post(
            "/admin/blog-ideas",
            headers=_admin_headers(),
            json=payload,
        )
        assert resp.status_code == 200
        assert resp.json()["positioning_notes"] == ["Note 1", "Note 2"]

    def test_invalid_title_empty(self, client: TestClient) -> None:
        resp = client.post(
            "/admin/blog-ideas",
            headers=_admin_headers(),
            json=_create_payload(title=""),
        )
        assert resp.status_code == 422

    def test_invalid_title_too_long(self, client: TestClient) -> None:
        resp = client.post(
            "/admin/blog-ideas",
            headers=_admin_headers(),
            json=_create_payload(title="x" * 241),
        )
        assert resp.status_code == 422


class TestUpdateIdea:
    """PATCH /admin/blog-ideas/{idea_id}"""

    def test_approve(
        self, client: TestClient, test_repo: BlogIdeaRepository
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Approve", angle="A", target_reader="D", article_goal="G"
            )
        )
        resp = client.patch(
            f"/admin/blog-ideas/{idea.id}",
            headers=_admin_headers(),
            json={"status": "approved", "feedback": "Looks good"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "approved"
        assert data["feedback"] == "Looks good"

    def test_reject(
        self, client: TestClient, test_repo: BlogIdeaRepository
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Reject", angle="A", target_reader="D", article_goal="G"
            )
        )
        resp = client.patch(
            f"/admin/blog-ideas/{idea.id}",
            headers=_admin_headers(),
            json={"status": "rejected"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"

    def test_update_outline_status(
        self, client: TestClient, test_repo: BlogIdeaRepository
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Outline Upd", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        resp = client.patch(
            f"/admin/blog-ideas/{idea.id}",
            headers=_admin_headers(),
            json={"outline_status": "approved"},
        )
        assert resp.status_code == 200
        assert resp.json()["outline_status"] == "approved"

    def test_update_draft_status(
        self, client: TestClient, test_repo: BlogIdeaRepository
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Draft Upd", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        resp = client.patch(
            f"/admin/blog-ideas/{idea.id}",
            headers=_admin_headers(),
            json={"draft_status": "approved"},
        )
        assert resp.status_code == 200
        assert resp.json()["draft_status"] == "approved"

    def test_not_found(self, client: TestClient) -> None:
        resp = client.patch(
            "/admin/blog-ideas/nonexistent",
            headers=_admin_headers(),
            json={"status": "approved"},
        )
        assert resp.status_code == 404


# =========================================================================
# Route Tests — Batch / Schedule
# =========================================================================


class TestBatchApprove:
    """POST /admin/blog-ideas/batch/approve"""

    def test_approve_multiple(
        self, client: TestClient, test_repo: BlogIdeaRepository
    ) -> None:
        i1 = test_repo.create(
            BlogIdeaCreate(
                title="A", angle="A", target_reader="D", article_goal="G"
            )
        )
        i2 = test_repo.create(
            BlogIdeaCreate(
                title="B", angle="B", target_reader="D", article_goal="G"
            )
        )
        resp = client.post(
            "/admin/blog-ideas/batch/approve",
            headers=_admin_headers(),
            json={"ids": [i1.id, i2.id]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["status"] == "approved"
        assert data[1]["status"] == "approved"

    def test_partial_missing(
        self, client: TestClient, test_repo: BlogIdeaRepository
    ) -> None:
        i1 = test_repo.create(
            BlogIdeaCreate(
                title="A", angle="A", target_reader="D", article_goal="G"
            )
        )
        resp = client.post(
            "/admin/blog-ideas/batch/approve",
            headers=_admin_headers(),
            json={"ids": [i1.id, "nonexistent"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["status"] == "approved"
        assert data[1]["status"] == "not_found"

    def test_empty_ids(self, client: TestClient) -> None:
        resp = client.post(
            "/admin/blog-ideas/batch/approve",
            headers=_admin_headers(),
            json={"ids": []},
        )
        assert resp.status_code == 200
        assert resp.json() == []


class TestSchedulePublish:
    """PATCH /admin/blog-ideas/{idea_id}/schedule"""

    def test_set_date(
        self, client: TestClient, test_repo: BlogIdeaRepository
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Sched", angle="A", target_reader="D", article_goal="G"
            )
        )
        resp = client.patch(
            f"/admin/blog-ideas/{idea.id}/schedule",
            headers=_admin_headers(),
            json={"scheduled_at": "2026-12-01T00:00:00Z"},
        )
        assert resp.status_code == 200
        assert resp.json()["scheduled_at"] is not None

    def test_not_found(self, client: TestClient) -> None:
        resp = client.patch(
            "/admin/blog-ideas/nonexistent/schedule",
            headers=_admin_headers(),
            json={"scheduled_at": "2026-12-01T00:00:00Z"},
        )
        assert resp.status_code == 404


# =========================================================================
# Route Tests — Pipeline Stage Dispatchers
#
# These endpoints use `_dispatch_or_run_generation` which for in-memory
# repos calls the task function directly. We patch the Celery tasks at
# their source module (backend.app.tasks) so the lazy import inside the
# route handler picks up our mock.
# =========================================================================


class TestGenerateOutline:
    """POST /admin/blog-ideas/{idea_id}/generate-outline"""

    @patch("backend.app.tasks.generate_blog_outline_task")
    def test_success(
        self,
        mock_task: MagicMock,
        client: TestClient,
        test_repo: BlogIdeaRepository,
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Gen Outline", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        test_repo.update(idea.id, BlogIdeaUpdate(status="approved"))
        mock_task.return_value = {"status": "ok"}

        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/generate-outline",
            headers=_admin_headers(),
            json={},
        )
        assert resp.status_code == 200
        mock_task.assert_called_once_with(idea_id=idea.id)

    def test_not_found(self, client: TestClient) -> None:
        resp = client.post(
            "/admin/blog-ideas/nonexistent/generate-outline",
            headers=_admin_headers(),
            json={},
        )
        assert resp.status_code == 404

    def test_requires_approved_idea(
        self, client: TestClient, test_repo: BlogIdeaRepository
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Pending", angle="A", target_reader="D", article_goal="G"
            )
        )
        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/generate-outline",
            headers=_admin_headers(),
            json={},
        )
        assert resp.status_code == 400
        assert "requires an approved idea" in resp.text.lower()


class TestGenerateDraft:
    """POST /admin/blog-ideas/{idea_id}/generate-draft"""

    @patch("backend.app.tasks.generate_blog_draft_task")
    def test_success(
        self,
        mock_task: MagicMock,
        client: TestClient,
        test_repo: BlogIdeaRepository,
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Gen Draft", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        test_repo.update(idea.id, BlogIdeaUpdate(status="approved"))
        test_repo.set_outline(
            idea.id,
            [OutlineSection(section="Intro", points=["P1"])],
            status="approved",
        )
        mock_task.return_value = {"status": "ok"}

        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/generate-draft",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        mock_task.assert_called_once_with(idea_id=idea.id)

    def test_not_found(self, client: TestClient) -> None:
        resp = client.post(
            "/admin/blog-ideas/nonexistent/generate-draft",
            headers=_admin_headers(),
        )
        assert resp.status_code == 404

    def test_requires_approved_outline(
        self, client: TestClient, test_repo: BlogIdeaRepository
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="No Outline", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        test_repo.update(idea.id, BlogIdeaUpdate(status="approved"))
        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/generate-draft",
            headers=_admin_headers(),
        )
        assert resp.status_code == 400
        assert "requires an approved outline" in resp.text.lower()


class TestReviewTechnical:
    """POST /admin/blog-ideas/{idea_id}/review-technical"""

    @patch("backend.app.tasks.generate_technical_review_task")
    def test_success(
        self,
        mock_task: MagicMock,
        client: TestClient,
        test_repo: BlogIdeaRepository,
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Tech Rev", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        test_repo.update(idea.id, BlogIdeaUpdate(status="approved"))
        test_repo.set_outline(
            idea.id,
            [OutlineSection(section="Intro", points=["P1"])],
            status="approved",
        )
        test_repo.set_draft(idea.id, "# Draft", status="approved")
        mock_task.return_value = {"status": "ok"}

        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/review-technical",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        mock_task.assert_called_once_with(idea_id=idea.id)

    def test_not_found(self, client: TestClient) -> None:
        resp = client.post(
            "/admin/blog-ideas/nonexistent/review-technical",
            headers=_admin_headers(),
        )
        assert resp.status_code == 404

    def test_requires_approved_draft(
        self, client: TestClient, test_repo: BlogIdeaRepository
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="No Draft", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        test_repo.update(idea.id, BlogIdeaUpdate(status="approved"))
        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/review-technical",
            headers=_admin_headers(),
        )
        assert resp.status_code == 400
        assert "requires an approved draft" in resp.text.lower()


class TestGenerateMarketing:
    """POST /admin/blog-ideas/{idea_id}/generate-marketing"""

    @patch("backend.app.tasks.generate_marketing_metadata_task")
    def test_success(
        self,
        mock_task: MagicMock,
        client: TestClient,
        test_repo: BlogIdeaRepository,
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Mkt Gen", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        test_repo.update(idea.id, BlogIdeaUpdate(status="approved"))
        test_repo.set_outline(
            idea.id,
            [OutlineSection(section="Intro", points=["P1"])],
            status="approved",
        )
        test_repo.set_draft(idea.id, "# Draft", status="approved")
        mock_task.return_value = {"status": "ok"}

        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/generate-marketing",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        mock_task.assert_called_once_with(idea_id=idea.id)

    def test_not_found(self, client: TestClient) -> None:
        resp = client.post(
            "/admin/blog-ideas/nonexistent/generate-marketing",
            headers=_admin_headers(),
        )
        assert resp.status_code == 404

    def test_requires_approved_draft(
        self, client: TestClient, test_repo: BlogIdeaRepository
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="No Draft Mkt", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        test_repo.update(idea.id, BlogIdeaUpdate(status="approved"))
        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/generate-marketing",
            headers=_admin_headers(),
        )
        assert resp.status_code == 400
        assert "requires an approved draft" in resp.text.lower()


class TestPublishToBlog:
    """POST /admin/blog-ideas/{idea_id}/publish-to-blog"""

    def test_no_blog_repo(self, client: TestClient) -> None:
        """When blog_repository is None, returns 500."""
        resp = client.post(
            "/admin/blog-ideas/idea_1/publish-to-blog",
            headers=_admin_headers(),
        )
        assert resp.status_code == 500
        assert "blog repository is not configured" in resp.text.lower()


class TestGenerateThumbnail:
    """POST /admin/blog-ideas/{idea_id}/generate-thumbnail"""

    @patch("backend.app.llm.thumbnail.generate_thumbnail")
    def test_not_found(
        self, mock_gen: MagicMock, client: TestClient
    ) -> None:
        resp = client.post(
            "/admin/blog-ideas/nonexistent/generate-thumbnail",
            headers=_admin_headers(),
        )
        assert resp.status_code == 404

    @patch("backend.app.llm.thumbnail.generate_thumbnail")
    def test_requires_draft(
        self,
        mock_gen: MagicMock,
        client: TestClient,
        test_repo: BlogIdeaRepository,
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Thumb", angle="A", target_reader="D", article_goal="G"
            )
        )
        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/generate-thumbnail",
            headers=_admin_headers(),
        )
        assert resp.status_code == 400
        assert "draft required" in resp.text.lower()

    @patch("backend.app.llm.thumbnail.generate_thumbnail")
    def test_success(
        self,
        mock_gen: MagicMock,
        client: TestClient,
        test_repo: BlogIdeaRepository,
    ) -> None:
        mock_gen.return_value = "https://example.com/thumb.png"
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Thumb Success", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        test_repo.set_draft(idea.id, "# Draft content\n\nMore text.")
        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/generate-thumbnail",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["image_url"] == "https://example.com/thumb.png"

    @patch("backend.app.llm.thumbnail.generate_thumbnail")
    def test_failure_returns_500(
        self,
        mock_gen: MagicMock,
        client: TestClient,
        test_repo: BlogIdeaRepository,
    ) -> None:
        mock_gen.return_value = None
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Thumb Fail", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        test_repo.set_draft(idea.id, "# Draft")
        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/generate-thumbnail",
            headers=_admin_headers(),
        )
        assert resp.status_code == 500
        assert "thumbnail generation failed" in resp.text.lower()


# =========================================================================
# Route Tests — Async Endpoints
# =========================================================================


class TestListClaims:
    """GET /admin/blog-ideas/{idea_id}/claims"""

    def test_no_claims_repo_returns_empty(self, client: TestClient) -> None:
        resp = client.get(
            "/admin/blog-ideas/idea_1/claims", headers=_admin_headers()
        )
        assert resp.status_code == 200
        assert resp.json() == []


class TestListAiRuns:
    """GET /admin/blog-ideas/{idea_id}/ai-runs"""

    def test_no_ai_runs_repo_returns_empty(self, client: TestClient) -> None:
        resp = client.get(
            "/admin/blog-ideas/idea_1/ai-runs", headers=_admin_headers()
        )
        assert resp.status_code == 200
        assert resp.json() == []


class TestExtractClaims:
    """POST /admin/blog-ideas/{idea_id}/extract-claims"""

    def test_no_claims_repo_returns_500(self, client: TestClient) -> None:
        resp = client.post(
            "/admin/blog-ideas/idea_1/extract-claims",
            headers=_admin_headers(),
        )
        assert resp.status_code == 500
        assert "not configured" in resp.text.lower()


class TestExtractClaimsWithRepo:
    """POST /admin/blog-ideas/{idea_id}/extract-claims — with claims repo."""

    @pytest.fixture
    def app_with_claims_repo(
        self, test_repo: BlogIdeaRepository, test_settings: Settings
    ) -> FastAPI:
        return _build_test_app(
            repo=test_repo,
            settings=test_settings,
            claims_repo=MagicMock(),
        )

    @pytest.fixture
    def claims_client(self, app_with_claims_repo: FastAPI) -> TestClient:
        return TestClient(app_with_claims_repo)

    def test_not_found(
        self, claims_client: TestClient
    ) -> None:
        resp = claims_client.post(
            "/admin/blog-ideas/nonexistent/extract-claims",
            headers=_admin_headers(),
        )
        assert resp.status_code == 404

    def test_no_draft(
        self, claims_client: TestClient, test_repo: BlogIdeaRepository
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="No Draft", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        resp = claims_client.post(
            f"/admin/blog-ideas/{idea.id}/extract-claims",
            headers=_admin_headers(),
        )
        assert resp.status_code == 400
        assert "draft markdown is required" in resp.text.lower()


class TestGetGenerationJob:
    """GET /admin/blog-ideas/generation-jobs/{task_id}"""

    def test_no_jobs_repo_returns_404(self, client: TestClient) -> None:
        resp = client.get(
            "/admin/blog-ideas/generation-jobs/task_1",
            headers=_admin_headers(),
        )
        assert resp.status_code == 404


class TestUpdateClaim:
    """PATCH /admin/blog-ideas/claims/{claim_id}"""

    def test_no_claims_repo_returns_500(self, client: TestClient) -> None:
        resp = client.patch(
            "/admin/blog-ideas/claims/claim_1",
            headers=_admin_headers(),
            json={"status": "supported"},
        )
        assert resp.status_code == 500
        assert "not configured" in resp.text.lower()


class TestSuggestLinks:
    """GET /admin/blog-ideas/{idea_id}/suggest-links"""

    # The route imports BlogRepository and suggest_internal_links lazily
    # inside the function body. We patch at the source modules.
    @patch("backend.app.llm.internal_links.suggest_internal_links")
    @patch("backend.app.blog.BlogRepository")
    def test_success(
        self,
        mock_blog_repo: MagicMock,
        mock_suggest: MagicMock,
        client: TestClient,
        test_repo: BlogIdeaRepository,
    ) -> None:
        mock_suggest.return_value = []
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Suggest Links", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        resp = client.get(
            f"/admin/blog-ideas/{idea.id}/suggest-links",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        assert resp.json() == []


# =========================================================================
# Route Tests — run-next State Machine
#
# Every branch of the pipeline decision tree.
# We patch Celery task functions at their source module so the lazy import
# inside the route handler picks up our mock.
# =========================================================================


class TestRunNext:
    """POST /admin/blog-ideas/{idea_id}/run-next"""

    # -- Edge cases -------------------------------------------------------

    def test_idea_not_found(self, client: TestClient) -> None:
        resp = client.post(
            "/admin/blog-ideas/nonexistent/run-next",
            headers=_admin_headers(),
        )
        assert resp.status_code == 404

    def test_already_published(
        self, client: TestClient, test_repo: BlogIdeaRepository
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Published", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        test_repo.link_published_post(idea.id, "post_existing")
        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/run-next",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["action"] == "done"
        assert "already published" in resp.json()["message"].lower()

    # -- Gate 1: Idea approval --------------------------------------------

    @patch("backend.app.tasks.generate_blog_outline_task")
    def test_pending_idea_approves_and_dispatches_outline(
        self,
        mock_task: MagicMock,
        client: TestClient,
        test_repo: BlogIdeaRepository,
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Pending Idea", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        mock_task.return_value = {"action": "dispatched"}

        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/run-next",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        mock_task.assert_called_once_with(idea_id=idea.id)

        # Verify idea was approved
        refreshed = test_repo.get_by_id(idea.id)
        assert refreshed is not None
        assert refreshed.status == "approved"

    def test_rejected_idea_returns_blocked(
        self, client: TestClient, test_repo: BlogIdeaRepository
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Rejected Idea", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        test_repo.update(idea.id, BlogIdeaUpdate(status="rejected"))
        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/run-next",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["action"] == "blocked"
        assert "rejected" in resp.json()["message"].lower()

    # -- Gate 2: Outline approval -----------------------------------------

    @patch("backend.app.tasks.generate_blog_draft_task")
    def test_outline_pending_with_sections(
        self,
        mock_task: MagicMock,
        client: TestClient,
        test_repo: BlogIdeaRepository,
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Outline Done", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        test_repo.update(idea.id, BlogIdeaUpdate(status="approved"))
        test_repo.set_outline(
            idea.id,
            [OutlineSection(section="Intro", points=["P1"])],
            status="pending",
        )
        mock_task.return_value = {"action": "dispatched"}

        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/run-next",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        mock_task.assert_called_once_with(idea_id=idea.id)

        # Outline should be approved
        refreshed = test_repo.get_by_id(idea.id)
        assert refreshed is not None
        assert refreshed.outline_status == "approved"

    @patch("backend.app.tasks.generate_blog_outline_task")
    def test_no_outline_sections(
        self,
        mock_task: MagicMock,
        client: TestClient,
        test_repo: BlogIdeaRepository,
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="No Outline", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        test_repo.update(idea.id, BlogIdeaUpdate(status="approved"))
        mock_task.return_value = {"action": "dispatched"}

        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/run-next",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        mock_task.assert_called_once_with(idea_id=idea.id)

    # -- Gate 3: Draft approval -------------------------------------------

    @patch("backend.app.tasks.generate_technical_review_task")
    def test_draft_pending_with_content(
        self,
        mock_task: MagicMock,
        client: TestClient,
        test_repo: BlogIdeaRepository,
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Draft Done", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        test_repo.update(idea.id, BlogIdeaUpdate(status="approved"))
        test_repo.set_outline(
            idea.id,
            [OutlineSection(section="Intro", points=["P1"])],
            status="approved",
        )
        test_repo.set_draft(idea.id, "# Full draft", status="pending")
        mock_task.return_value = {"action": "dispatched"}

        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/run-next",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        mock_task.assert_called_once_with(idea_id=idea.id)

        # Draft should now be approved
        refreshed = test_repo.get_by_id(idea.id)
        assert refreshed is not None
        assert refreshed.draft_status == "approved"

    @patch("backend.app.tasks.generate_blog_draft_task")
    def test_no_draft_markdown(
        self,
        mock_task: MagicMock,
        client: TestClient,
        test_repo: BlogIdeaRepository,
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="No Draft", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        test_repo.update(idea.id, BlogIdeaUpdate(status="approved"))
        test_repo.set_outline(
            idea.id,
            [OutlineSection(section="Intro", points=["P1"])],
            status="approved",
        )
        mock_task.return_value = {"action": "dispatched"}

        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/run-next",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        mock_task.assert_called_once_with(idea_id=idea.id)

    # -- Gate 4: Technical review -----------------------------------------

    @patch("backend.app.tasks.generate_technical_review_task")
    def test_no_technical_review(
        self,
        mock_task: MagicMock,
        client: TestClient,
        test_repo: BlogIdeaRepository,
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="No Tech Rev", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        test_repo.update(idea.id, BlogIdeaUpdate(status="approved"))
        test_repo.set_outline(
            idea.id,
            [OutlineSection(section="Intro", points=["P1"])],
            status="approved",
        )
        test_repo.set_draft(idea.id, "# Draft", status="approved")
        mock_task.return_value = {"action": "dispatched"}

        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/run-next",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        mock_task.assert_called_once_with(idea_id=idea.id)

    @patch("backend.app.tasks.generate_marketing_metadata_task")
    def test_technical_review_pending(
        self,
        mock_task: MagicMock,
        client: TestClient,
        test_repo: BlogIdeaRepository,
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Tech Rev Pending", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        test_repo.update(idea.id, BlogIdeaUpdate(status="approved"))
        test_repo.set_outline(
            idea.id,
            [OutlineSection(section="Intro", points=["P1"])],
            status="approved",
        )
        test_repo.set_draft(idea.id, "# Draft", status="approved")
        test_repo.set_technical_review(
            idea.id, {"risk": "low"}, status="pending"
        )
        mock_task.return_value = {"action": "dispatched"}

        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/run-next",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        mock_task.assert_called_once_with(idea_id=idea.id)

        # Technical review should now be approved
        refreshed = test_repo.get_by_id(idea.id)
        assert refreshed is not None
        assert refreshed.technical_review_status == "approved"

    @patch("backend.app.tasks.generate_technical_review_task")
    def test_technical_review_rejected(
        self,
        mock_task: MagicMock,
        client: TestClient,
        test_repo: BlogIdeaRepository,
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Tech Rev Rej", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        test_repo.update(idea.id, BlogIdeaUpdate(status="approved"))
        test_repo.set_outline(
            idea.id,
            [OutlineSection(section="Intro", points=["P1"])],
            status="approved",
        )
        test_repo.set_draft(idea.id, "# Draft", status="approved")
        test_repo.set_technical_review(
            idea.id, {"risk": "high"}, status="rejected"
        )
        mock_task.return_value = {"action": "dispatched"}

        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/run-next",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        mock_task.assert_called_once_with(idea_id=idea.id)

    # -- Gate 5: Marketing metadata ---------------------------------------

    @patch("backend.app.tasks.generate_marketing_metadata_task")
    def test_no_marketing_metadata(
        self,
        mock_task: MagicMock,
        client: TestClient,
        test_repo: BlogIdeaRepository,
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="No Mkt", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        test_repo.update(idea.id, BlogIdeaUpdate(status="approved"))
        test_repo.set_outline(
            idea.id,
            [OutlineSection(section="Intro", points=["P1"])],
            status="approved",
        )
        test_repo.set_draft(idea.id, "# Draft", status="approved")
        test_repo.set_technical_review(
            idea.id, {"risk": "low"}, status="approved"
        )
        mock_task.return_value = {"action": "dispatched"}

        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/run-next",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        mock_task.assert_called_once_with(idea_id=idea.id)

    @patch("backend.app.blog_ideas._run_next_extract_claims",
           new_callable=AsyncMock)
    def test_marketing_pending(
        self,
        mock_extract: AsyncMock,
        client: TestClient,
        test_repo: BlogIdeaRepository,
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Mkt Pending", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        test_repo.update(idea.id, BlogIdeaUpdate(status="approved"))
        test_repo.set_outline(
            idea.id,
            [OutlineSection(section="Intro", points=["P1"])],
            status="approved",
        )
        test_repo.set_draft(idea.id, "# Draft", status="approved")
        test_repo.set_technical_review(
            idea.id, {"risk": "low"}, status="approved"
        )
        test_repo.set_marketing_metadata(
            idea.id, {"seo_title": "SEO"}, status="pending"
        )
        mock_extract.return_value = {
            "action": "generated",
            "next_stage": "claims",
        }

        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/run-next",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["action"] == "generated"
        assert resp.json()["next_stage"] == "claims"

        # Marketing should be approved
        refreshed = test_repo.get_by_id(idea.id)
        assert refreshed is not None
        assert refreshed.marketing_status == "approved"

    @patch("backend.app.tasks.generate_marketing_metadata_task")
    def test_marketing_rejected(
        self,
        mock_task: MagicMock,
        client: TestClient,
        test_repo: BlogIdeaRepository,
    ) -> None:
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Mkt Rej", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        test_repo.update(idea.id, BlogIdeaUpdate(status="approved"))
        test_repo.set_outline(
            idea.id,
            [OutlineSection(section="Intro", points=["P1"])],
            status="approved",
        )
        test_repo.set_draft(idea.id, "# Draft", status="approved")
        test_repo.set_technical_review(
            idea.id, {"risk": "low"}, status="approved"
        )
        test_repo.set_marketing_metadata(
            idea.id, {"seo_title": "SEO"}, status="rejected"
        )
        mock_task.return_value = {"action": "dispatched"}

        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/run-next",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        mock_task.assert_called_once_with(idea_id=idea.id)

    # -- Gate 6: Claims -> Publish (blocked because no blog_repo) ---------

    def test_ready_for_publish_but_no_blog_repo(
        self, client: TestClient, test_repo: BlogIdeaRepository
    ) -> None:
        """When blog_repository is None, publish gate returns blocked."""
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Ready Pub", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        test_repo.update(idea.id, BlogIdeaUpdate(status="approved"))
        test_repo.set_outline(
            idea.id,
            [OutlineSection(section="Intro", points=["P1"])],
            status="approved",
        )
        test_repo.set_draft(idea.id, "# Draft", status="approved")
        test_repo.set_technical_review(
            idea.id, {"risk": "low"}, status="approved"
        )
        test_repo.set_marketing_metadata(
            idea.id, {"seo_title": "SEO"}, status="approved"
        )

        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/run-next",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["action"] == "blocked"


# =========================================================================
# Route Tests — Streaming (generate-stream/idea)
# =========================================================================


class TestGenerateIdeaStream:
    """POST /admin/blog-ideas/generate-stream/idea"""

    @pytest.mark.asyncio
    async def test_auth_required(self, async_client: AsyncClient) -> None:
        resp = await async_client.post(
            "/admin/blog-ideas/generate-stream/idea",
            json={
                "project_name": "Test",
                "project_summary": "A test project",
            },
        )
        assert resp.status_code == 401


# =========================================================================
# Additional coverage: generate-ideas, dispatch, jobs, claims, ai-runs
# =========================================================================


class TestGenerateIdeas:
    """POST /admin/blog-ideas/generate"""

    @patch("backend.app.tasks.generate_blog_idea_task")
    def test_success(
        self,
        mock_task: MagicMock,
        client: TestClient,
    ) -> None:
        mock_task.return_value = {"idea": {"title": "Generated Idea"}}
        resp = client.post(
            "/admin/blog-ideas/generate",
            headers=_admin_headers(),
            json={
                "project_name": "My Project",
                "project_summary": "A great project",
                "ai_capabilities": "LLM, vision",
                "technical_highlights": "Structured outputs",
                "business_value": "Saves time",
            },
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["idea"]["title"] == "Generated Idea"
        mock_task.assert_called_once()

    def test_requires_auth(self, client: TestClient) -> None:
        resp = client.post(
            "/admin/blog-ideas/generate",
            json={
                "project_name": "Test",
                "project_summary": "Test project",
            },
        )
        assert resp.status_code == 401


class TestPublishToBlogWithRepo:
    """POST /admin/blog-ideas/{idea_id}/publish-to-blog with blog repo."""

    @patch("backend.app.blog_publish.publish_idea_to_blog")
    def test_publish_success(
        self,
        mock_publish: MagicMock,
        test_repo: BlogIdeaRepository,
        test_settings: Settings,
    ) -> None:
        mock_publish.return_value = ("post_42", "test-slug", False)
        idea = test_repo.create(
            BlogIdeaCreate(
                title="Pub", angle="A", target_reader="D", article_goal="G"
            )
        )
        app = _build_test_app(
            repo=test_repo,
            settings=test_settings,
            blog_repo=MagicMock(),
            claims_repo=MagicMock(),
        )
        client = TestClient(app)
        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/publish-to-blog",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["blog_post_id"] == "post_42"
        assert data["slug"] == "test-slug"
        assert data["already_linked"] is False

    @patch("backend.app.blog_publish.publish_idea_to_blog")
    def test_publish_not_found(
        self,
        mock_publish: MagicMock,
        test_repo: BlogIdeaRepository,
        test_settings: Settings,
    ) -> None:
        from fastapi import HTTPException
        # When idea doesn't exist, publish_idea_to_blog raises 404
        mock_publish.side_effect = HTTPException(status_code=404, detail="Blog idea not found")
        app = _build_test_app(
            repo=test_repo,
            settings=test_settings,
            blog_repo=MagicMock(),
            claims_repo=MagicMock(),
        )
        client = TestClient(app)
        resp = client.post(
            "/admin/blog-ideas/nonexistent/publish-to-blog",
            headers=_admin_headers(),
        )
        assert resp.status_code == 404


class TestGenerationJobsWithRepo:
    """GET /admin/blog-ideas/generation-jobs/{task_id} with job repo."""

    def test_job_found(
        self,
        test_repo: BlogIdeaRepository,
        test_settings: Settings,
    ) -> None:
        mock_jobs = MagicMock()
        from backend.app.generation_jobs import GenerationJob

        mock_jobs.get_by_celery_task_id.return_value = GenerationJob(
            id="job_1",
            blog_idea_id="idea_1",
            stage="outline",
            celery_task_id="celery_job_1",
            status="queued",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        app = _build_test_app(
            repo=test_repo,
            settings=test_settings,
            jobs_repo=mock_jobs,
        )
        client = TestClient(app)
        resp = client.get(
            "/admin/blog-ideas/generation-jobs/celery_job_1",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "job_1"
        assert data["stage"] == "outline"
        mock_jobs.get_by_celery_task_id.assert_called_once_with("celery_job_1")

    def test_job_not_found(
        self,
        test_repo: BlogIdeaRepository,
        test_settings: Settings,
    ) -> None:
        mock_jobs = MagicMock()
        mock_jobs.get_by_celery_task_id.return_value = None
        app = _build_test_app(
            repo=test_repo,
            settings=test_settings,
            jobs_repo=mock_jobs,
        )
        client = TestClient(app)
        resp = client.get(
            "/admin/blog-ideas/generation-jobs/unknown",
            headers=_admin_headers(),
        )
        assert resp.status_code == 404


class TestUpdateClaimWithRepo:
    """PATCH /admin/blog-ideas/claims/{claim_id} with claims repo."""

    def test_update_success(
        self,
        test_repo: BlogIdeaRepository,
        test_settings: Settings,
    ) -> None:
        mock_claims = MagicMock()
        from backend.app.blog_claims import BlogClaim

        from backend.app.blog_claims import BlogClaim
        from datetime import UTC, datetime
        now = datetime.now(UTC)
        mock_claims.update.return_value = BlogClaim(
            id="claim_1",
            blog_idea_id="idea_1",
            claim_text="Test claim",
            claim_type="opinion",
            status="supported",
            created_at=now,
            updated_at=now,
        )
        app = _build_test_app(
            repo=test_repo,
            settings=test_settings,
            claims_repo=mock_claims,
        )
        client = TestClient(app)
        resp = client.patch(
            "/admin/blog-ideas/claims/claim_1",
            headers=_admin_headers(),
            json={"status": "supported"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "claim_1"
        assert data["status"] == "supported"
        mock_claims.update.assert_called_once()

    def test_update_not_found(
        self,
        test_repo: BlogIdeaRepository,
        test_settings: Settings,
    ) -> None:
        mock_claims = MagicMock()
        mock_claims.update.return_value = None
        app = _build_test_app(
            repo=test_repo,
            settings=test_settings,
            claims_repo=mock_claims,
        )
        client = TestClient(app)
        resp = client.patch(
            "/admin/blog-ideas/claims/missing_claim",
            headers=_admin_headers(),
            json={"status": "supported"},
        )
        assert resp.status_code == 404


class TestListAiRunsWithRepo:
    """GET /admin/blog-ideas/{idea_id}/ai-runs with repo."""

    def test_list_success(
        self,
        test_repo: BlogIdeaRepository,
        test_settings: Settings,
    ) -> None:
        mock_ai_runs = MagicMock()
        from backend.app.ai_runs import AiRun

        mock_ai_runs.list_for_entity.return_value = [
            AiRun(
                id="run_1",
                entity_type="blog_idea",
                entity_id="idea_1",
                model="gpt-4o",
                provider="openai",
                prompt_name="test",
                prompt_version="1.0",
                status="completed",
                input_payload={"project_name": "Test"},
                created_at=datetime.now(UTC),
            )
        ]
        app = _build_test_app(
            repo=test_repo,
            settings=test_settings,
            ai_runs_repo=mock_ai_runs,
        )
        client = TestClient(app)
        resp = client.get(
            "/admin/blog-ideas/idea_1/ai-runs",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "run_1"
        mock_ai_runs.list_for_entity.assert_called_once_with(
            "blog_idea", "idea_1"
        )


class TestDispatchGenerationTask:
    """Direct tests for ``_dispatch_generation_task``."""

    def test_raises_202_with_task_id(self) -> None:
        """Always raises HTTP 202 with the provided task_id in detail."""
        from fastapi import HTTPException
        from backend.app.blog_ideas import _dispatch_generation_task

        with pytest.raises(HTTPException) as exc_info:
            _dispatch_generation_task(
                stage="outline",
                idea_id="idea_1",
                celery_task_id="celery_abc",
                message="Generation started",
                jobs_repository=None,
                track_job=False,
            )
        assert exc_info.value.status_code == 202
        detail = exc_info.value.detail
        assert detail["task_id"] == "celery_abc"
        assert detail["message"] == "Generation started"

    def test_creates_job_when_track_job_with_repo(self) -> None:
        """When track_job=True and jobs_repository is provided, creates a job."""
        from fastapi import HTTPException
        from backend.app.blog_ideas import _dispatch_generation_task

        mock_jobs = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            _dispatch_generation_task(
                stage="draft",
                idea_id="idea_2",
                celery_task_id="celery_def",
                message="Draft generation",
                jobs_repository=mock_jobs,
                track_job=True,
            )
        assert exc_info.value.status_code == 202
        mock_jobs.create_queued.assert_called_once_with(
            blog_idea_id="idea_2",
            stage="draft",
            celery_task_id="celery_def",
        )


class TestRowToIdea:
    """Direct tests for ``_row_to_idea`` JSON parsing helper."""

    def test_simple_row(self) -> None:
        from backend.app.blog_ideas import _row_to_idea
        now = datetime.now(UTC)
        row = {
            "id": "idea_1",
            "title": "Test",
            "angle": "Angle",
            "target_reader": "Devs",
            "article_goal": "Goal",
            "source": "manual",
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        }
        idea = _row_to_idea(row)
        assert idea.id == "idea_1"
        assert idea.positioning_notes == []

    def test_parses_positioning_notes(self) -> None:
        from backend.app.blog_ideas import _row_to_idea
        now = datetime.now(UTC)
        row = {
            "id": "idea_1",
            "title": "Test",
            "angle": "Angle",
            "target_reader": "Devs",
            "article_goal": "Goal",
            "positioning_notes": '["Note 1", "Note 2"]',
            "source": "manual",
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        }
        idea = _row_to_idea(row)
        assert idea.positioning_notes == ["Note 1", "Note 2"]

    def test_parses_outline_sections(self) -> None:
        from backend.app.blog_ideas import _row_to_idea
        now = datetime.now(UTC)
        row = {
            "id": "idea_1",
            "title": "Test",
            "angle": "Angle",
            "target_reader": "Devs",
            "article_goal": "Goal",
            "outline_sections": '[{"section": "Intro", "points": ["P1"]}]',
            "source": "manual",
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        }
        idea = _row_to_idea(row)
        assert len(idea.outline_sections) == 1
        assert idea.outline_sections[0].section == "Intro"

    def test_parses_technical_review(self) -> None:
        from backend.app.blog_ideas import _row_to_idea
        now = datetime.now(UTC)
        row = {
            "id": "idea_1",
            "title": "Test",
            "angle": "Angle",
            "target_reader": "Devs",
            "article_goal": "Goal",
            "technical_review": '{"risk": "low"}',
            "source": "manual",
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        }
        idea = _row_to_idea(row)
        assert idea.technical_review == {"risk": "low"}

    def test_parses_marketing_metadata(self) -> None:
        from backend.app.blog_ideas import _row_to_idea
        now = datetime.now(UTC)
        row = {
            "id": "idea_1",
            "title": "Test",
            "angle": "Angle",
            "target_reader": "Devs",
            "article_goal": "Goal",
            "marketing_metadata": '{"seo_title": "SEO"}',
            "source": "manual",
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        }
        idea = _row_to_idea(row)
        assert idea.marketing_metadata == {"seo_title": "SEO"}

    def test_parses_source_project_context(self) -> None:
        from backend.app.blog_ideas import _row_to_idea
        now = datetime.now(UTC)
        row = {
            "id": "idea_1",
            "title": "Test",
            "angle": "Angle",
            "target_reader": "Devs",
            "article_goal": "Goal",
            "source_project_context": '{"project": "Test"}',
            "source": "ai_generated",
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        }
        idea = _row_to_idea(row)
        assert idea.source_project_context == {"project": "Test"}

    def test_handles_invalid_json_gracefully(self) -> None:
        from backend.app.blog_ideas import _row_to_idea
        now = datetime.now(UTC)
        row = {
            "id": "idea_1",
            "title": "Test",
            "angle": "Angle",
            "target_reader": "Devs",
            "article_goal": "Goal",
            "positioning_notes": "{invalid json}",
            "source": "manual",
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        }
        idea = _row_to_idea(row)
        # Invalid JSON gracefully falls back to empty
        assert idea.positioning_notes == []


class TestDispatchOrRunGenerationPostgres:
    """Test the Postgres path of ``_dispatch_or_run_generation``."""

    def test_postgres_path_with_fake_success(self) -> None:
        """Postgres repo + llm_e2e_fake=True + successful task = returns result."""
        from backend.app.blog_ideas import (
            PostgresBlogIdeaRepository,
            _dispatch_or_run_generation,
        )

        # Mock the SQLAlchemy engine
        mock_engine = MagicMock()
        repo = PostgresBlogIdeaRepository(mock_engine)

        mock_task = MagicMock()
        mock_async_result = MagicMock()
        mock_async_result.ready.return_value = True
        mock_async_result.successful.return_value = True
        mock_async_result.get.return_value = {"outline": ["section 1"]}
        mock_task.apply_async.return_value = mock_async_result

        settings = Settings(
            environment="test",
            admin_boundary_secret=TEST_SECRET,
            llm_e2e_fake=True,
        )

        result = _dispatch_or_run_generation(
            repository=repo,
            task=mock_task,
            stage="outline",
            idea_id="idea_1",
            message="Outline generation",
            jobs_repository=None,
            kwargs={"idea_id": "idea_1"},
            settings=settings,
        )
        assert result == {"outline": ["section 1"]}
        mock_task.apply_async.assert_called_once()

    def test_postgres_path_with_pending_idea_id(self) -> None:
        """When idea_id starts with 'pending:', job gets a pending: prefix."""
        from backend.app.blog_ideas import (
            PostgresBlogIdeaRepository,
            _dispatch_or_run_generation,
        )

        mock_engine = MagicMock()
        repo = PostgresBlogIdeaRepository(mock_engine)

        mock_task = MagicMock()
        mock_async_result = MagicMock()
        mock_async_result.ready.return_value = True
        mock_async_result.successful.return_value = True
        mock_async_result.get.return_value = {"idea": "generated"}
        mock_task.apply_async.return_value = mock_async_result

        mock_jobs = MagicMock()

        settings = Settings(
            environment="test",
            admin_boundary_secret=TEST_SECRET,
            llm_e2e_fake=True,
        )

        result = _dispatch_or_run_generation(
            repository=repo,
            task=mock_task,
            stage="idea",
            idea_id="pending:",
            message="Idea generation",
            jobs_repository=mock_jobs,
            kwargs={"project_name": "Test"},
            settings=settings,
        )
        assert result == {"idea": "generated"}
        # Verify job was created with pending: prefix
        _, kwargs = mock_jobs.create_queued.call_args
        assert "pending:" in kwargs.get("blog_idea_id", "")

    def test_postgres_path_fake_failure_raises_500(self) -> None:
        """When llm_e2e_fake=True and task fails, raises HTTP 500."""
        from backend.app.blog_ideas import (
            PostgresBlogIdeaRepository,
            _dispatch_or_run_generation,
        )
        from fastapi import HTTPException

        mock_engine = MagicMock()
        repo = PostgresBlogIdeaRepository(mock_engine)

        mock_task = MagicMock()
        mock_async_result = MagicMock()
        mock_async_result.ready.return_value = True
        mock_async_result.successful.return_value = False
        mock_async_result.result = ValueError("Task failed")
        mock_task.apply_async.return_value = mock_async_result

        settings = Settings(
            environment="test",
            admin_boundary_secret=TEST_SECRET,
            llm_e2e_fake=True,
        )

        with pytest.raises(HTTPException) as exc_info:
            _dispatch_or_run_generation(
                repository=repo,
                task=mock_task,
                stage="draft",
                idea_id="idea_1",
                message="Draft generation",
                jobs_repository=None,
                kwargs={"idea_id": "idea_1"},
                settings=settings,
            )
        assert exc_info.value.status_code == 500


class TestRunNextComplexPaths:
    """Additional run-next paths: claims existing, publish, and extract claims."""

    def test_run_next_claims_exist_but_no_blog_repo(
        self,
        test_settings: Settings,
    ) -> None:
        """run-next with claims existing but no blog_repo returns blocked."""
        repo = BlogIdeaRepository()
        mock_claims = MagicMock()
        # Return some claims so the 'no claims' check fails
        from backend.app.blog_claims import BlogClaim
        now = datetime.now(UTC)
        mock_claims.list_for_idea.return_value = [
            BlogClaim(
                id="claim_1",
                blog_idea_id="idea_1",
                claim_text="Test claim",
                claim_type="opinion",
                status="supported",
                created_at=now,
                updated_at=now,
            )
        ]

        app = _build_test_app(
            repo=repo,
            settings=test_settings,
            claims_repo=mock_claims,
        )
        client = TestClient(app)

        idea = repo.create(
            BlogIdeaCreate(
                title="Claims Exit", angle="A", target_reader="D", article_goal="G"
            )
        )
        repo.update(idea.id, BlogIdeaUpdate(status="approved"))
        repo.set_outline(
            idea.id,
            [OutlineSection(section="Intro", points=["P1"])],
            status="approved",
        )
        repo.set_draft(idea.id, "# Draft", status="approved")
        repo.set_technical_review(idea.id, {"risk": "low"}, status="approved")
        repo.set_marketing_metadata(
            idea.id, {"seo_title": "SEO"}, status="approved"
        )

        resp = client.post(
            f"/admin/blog-ideas/{idea.id}/run-next",
            headers=_admin_headers(),
        )
        # No blog_repo → blocked
        assert resp.status_code == 200
        assert resp.json()["action"] == "blocked"

    def test_run_next_to_publish(
        self,
        test_settings: Settings,
    ) -> None:
        """Full run-next pipeline with blog_repo publishes successfully."""
        repo = BlogIdeaRepository()
        mock_claims = MagicMock()
        mock_blog = MagicMock()

        from backend.app.blog_claims import BlogClaim
        now = datetime.now(UTC)
        mock_claims.list_for_idea.return_value = [
            BlogClaim(
                id="claim_1",
                blog_idea_id="idea_1",
                claim_text="Test claim",
                claim_type="opinion",
                status="supported",
                created_at=now,
                updated_at=now,
            )
        ]

        app = _build_test_app(
            repo=repo,
            settings=test_settings,
            blog_repo=mock_blog,
            claims_repo=mock_claims,
        )
        client = TestClient(app)

        idea = repo.create(
            BlogIdeaCreate(
                title="Full Pub", angle="A", target_reader="D", article_goal="G"
            )
        )
        repo.update(idea.id, BlogIdeaUpdate(status="approved"))
        repo.set_outline(
            idea.id,
            [OutlineSection(section="Intro", points=["P1"])],
            status="approved",
        )
        repo.set_draft(idea.id, "# Draft", status="approved")
        repo.set_technical_review(idea.id, {"risk": "low"}, status="approved")
        repo.set_marketing_metadata(
            idea.id, {"seo_title": "SEO"}, status="approved"
        )

        # Mock the publish_idea_to_blog function
        with patch(
            "backend.app.blog_publish.publish_idea_to_blog",
            return_value=("post_99", "my-slug", False),
        ):
            resp = client.post(
                f"/admin/blog-ideas/{idea.id}/run-next",
                headers=_admin_headers(),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["action"] == "published"
        assert data["blog_post_id"] == "post_99"
        assert data["slug"] == "my-slug"

    def test_extract_claims_with_llm_service(
        self,
        test_settings: Settings,
    ) -> None:
        """Test the extract-claims route with mocked LLM service."""
        repo = BlogIdeaRepository()
        idea = repo.create(
            BlogIdeaCreate(
                title="Extract LLM", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        repo.set_draft(idea.id, "# Draft about AI testing.")

        mock_claims = MagicMock()
        mock_claims.replace_for_idea.return_value = []

        app = _build_test_app(
            repo=repo,
            settings=test_settings,
            claims_repo=mock_claims,
        )
        client = TestClient(app)

        # Mock llm_service_for_idea
        with patch(
            "backend.app.task_support.llm_service_for_idea",
            return_value=MagicMock(),
        ), patch(
            "backend.app.blog_ideas.extract_claims_with_llm",
            return_value=[],
        ), patch(
            "backend.app.blog_ideas.claims_from_extraction",
            return_value=[],
        ):
            resp = client.post(
                f"/admin/blog-ideas/{idea.id}/extract-claims",
                headers=_admin_headers(),
            )

        assert resp.status_code == 200

    def test_extract_claims_falls_back_to_heuristic(
        self,
        test_settings: Settings,
    ) -> None:
        """When LLM extraction fails, falls back to heuristic extraction."""
        repo = BlogIdeaRepository()
        idea = repo.create(
            BlogIdeaCreate(
                title="Extract Fallback", angle="A", target_reader="D",
                article_goal="G",
            )
        )
        repo.set_draft(idea.id, "# Draft about AI.")

        mock_claims = MagicMock()
        mock_claims.replace_for_idea.return_value = []

        app = _build_test_app(
            repo=repo,
            settings=test_settings,
            claims_repo=mock_claims,
        )
        client = TestClient(app)

        with patch(
            "backend.app.task_support.llm_service_for_idea",
            return_value=MagicMock(),
        ), patch(
            "backend.app.blog_ideas.extract_claims_with_llm",
            side_effect=ValueError("LLM failed"),
        ), patch(
            "backend.app.blog_ideas.heuristic_claims_from_draft",
            return_value=[],
        ):
            resp = client.post(
                f"/admin/blog-ideas/{idea.id}/extract-claims",
                headers=_admin_headers(),
            )

        assert resp.status_code == 200
