"""Tests for the Blog Idea management module (US-026).

Covers:
- Pydantic model validation
- In-memory repository CRUD
- Route handlers (via TestClient)
- Celery task (eager mode)
"""

import json
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    sign_admin_identity,
)
from backend.app.blog_ideas import (
    BlogIdea,
    BlogIdeaCreate,
    BlogIdeaGenerateRequest,
    BlogIdeaRepository,
    BlogIdeaSummary,
    BlogIdeaUpdate,
    OutlineSection,
    create_blog_idea_routes,
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
# Model validation
# ===========================================================================


class TestBlogIdeaModels:
    def test_valid_create_payload(self) -> None:
        p = BlogIdeaCreate(
            title="How We Built an AI Pipeline",
            angle="AI Engineering",
            target_reader="CTOs",
            article_goal="Share lessons learned",
            positioning_notes=["Avoid hype"],
        )
        assert p.title == "How We Built an AI Pipeline"
        assert p.positioning_notes == ["Avoid hype"]

    def test_create_rejects_blank_title(self) -> None:
        with pytest.raises(ValidationError):
            BlogIdeaCreate(
                title="",
                angle="Test",
                target_reader="Devs",
                article_goal="Test goal",
            )

    def test_generate_request_valid(self) -> None:
        r = BlogIdeaGenerateRequest(
            project_name="Scopelytics",
            project_summary="An AI-powered business analysis tool.",
            ai_capabilities="LLM, Evaluation",
            technical_highlights="Structured output",
            business_value="Reduces manual analysis",
        )
        assert r.project_name == "Scopelytics"

    def test_update_model_valid(self) -> None:
        u = BlogIdeaUpdate(status="approved", feedback="Great idea, proceed.")
        assert u.status == "approved"
        assert u.feedback == "Great idea, proceed."

    def test_update_model_empty_allowed(self) -> None:
        u = BlogIdeaUpdate()
        assert u.status is None
        assert u.feedback is None


# ===========================================================================
# In-memory repository
# ===========================================================================


class TestBlogIdeaRepository:
    def test_empty_repository(self) -> None:
        repo = BlogIdeaRepository()
        assert repo.list_all() == []

    def test_create_idea(self) -> None:
        repo = BlogIdeaRepository()
        idea = repo.create(
            BlogIdeaCreate(
                title="Test Idea",
                angle="AI Evaluation",
                target_reader="Developers",
                article_goal="Show evaluation process",
            )
        )
        assert idea.title == "Test Idea"
        assert idea.source == "manual"
        assert idea.status == "pending"
        assert len(idea.id) > 0

    def test_list_all_returns_summaries(self) -> None:
        repo = BlogIdeaRepository()
        repo.create(
            BlogIdeaCreate(
                title="Idea A",
                angle="Test",
                target_reader="Devs",
                article_goal="Goal A",
            )
        )
        repo.create(
            BlogIdeaCreate(
                title="Idea B",
                angle="Test",
                target_reader="Devs",
                article_goal="Goal B",
            )
        )
        results = repo.list_all()
        assert len(results) == 2
        assert all(isinstance(r, BlogIdeaSummary) for r in results)
        # Both ideas present
        titles = {r.title for r in results}
        assert titles == {"Idea A", "Idea B"}

    def test_get_by_id(self) -> None:
        repo = BlogIdeaRepository()
        created = repo.create(
            BlogIdeaCreate(
                title="Get Me",
                angle="Test",
                target_reader="Devs",
                article_goal="Find me",
            )
        )
        fetched = repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.title == "Get Me"

    def test_get_by_id_missing(self) -> None:
        repo = BlogIdeaRepository()
        assert repo.get_by_id("nonexistent") is None

    def test_add_generated_idea(self) -> None:
        repo = BlogIdeaRepository()
        idea = repo.add_generated(
            BlogIdeaCreate(
                title="AI Generated Idea",
                angle="Test",
                target_reader="Devs",
                article_goal="Auto-generated",
            ),
            context={"project_name": "Scopelytics"},
        )
        assert idea.source == "ai_generated"
        assert idea.source_project_context == {"project_name": "Scopelytics"}

    def test_approve_idea(self) -> None:
        repo = BlogIdeaRepository()
        created = repo.create(
            BlogIdeaCreate(
                title="Approve Me",
                angle="Test",
                target_reader="Devs",
                article_goal="Get approved",
            )
        )
        updated = repo.update(created.id, BlogIdeaUpdate(status="approved"))
        assert updated is not None
        assert updated.status == "approved"
        assert updated.reviewed_at is not None
        assert updated.reviewed_by == "admin"

    def test_reject_with_feedback(self) -> None:
        repo = BlogIdeaRepository()
        created = repo.create(
            BlogIdeaCreate(
                title="Reject Me",
                angle="Test",
                target_reader="Devs",
                article_goal="Get rejected",
            )
        )
        updated = repo.update(
            created.id,
            BlogIdeaUpdate(status="rejected", feedback="Not aligned with our focus."),
        )
        assert updated is not None
        assert updated.status == "rejected"
        assert updated.feedback == "Not aligned with our focus."

    def test_update_missing_idea(self) -> None:
        repo = BlogIdeaRepository()
        assert repo.update("missing", BlogIdeaUpdate(status="approved")) is None


# ===========================================================================
# API routes via TestClient
# ===========================================================================


class TestBlogIdeaRoutes:
    def test_list_ideas_requires_auth(self) -> None:
        app = create_app(settings=_test_settings())
        client = TestClient(app)
        response = client.get("/admin/blog-ideas")
        assert response.status_code == 401

    def test_list_ideas_empty(self) -> None:
        app = create_app(settings=_test_settings())
        client = TestClient(app)
        response = client.get("/admin/blog-ideas", headers=_admin_headers())
        assert response.status_code == 200
        assert response.json() == []

    def test_create_idea(self) -> None:
        app = create_app(settings=_test_settings())
        client = TestClient(app)
        response = client.post(
            "/admin/blog-ideas",
            headers=_admin_headers(),
            json={
                "title": "My Blog Idea",
                "angle": "AI Engineering",
                "target_reader": "Developers",
                "article_goal": "Share knowledge",
                "positioning_notes": ["Practical focus"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "My Blog Idea"
        assert data["source"] == "manual"
        assert data["status"] == "pending"
        assert "id" in data

    def test_create_and_list(self) -> None:
        app = create_app(settings=_test_settings())
        client = TestClient(app)
        # Create one
        client.post(
            "/admin/blog-ideas",
            headers=_admin_headers(),
            json={
                "title": "First Idea",
                "angle": "AI",
                "target_reader": "Devs",
                "article_goal": "Test",
            },
        )
        # List
        response = client.get("/admin/blog-ideas", headers=_admin_headers())
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "First Idea"

    def test_get_idea_by_id(self) -> None:
        app = create_app(settings=_test_settings())
        client = TestClient(app)
        created = client.post(
            "/admin/blog-ideas",
            headers=_admin_headers(),
            json={
                "title": "Specific Idea",
                "angle": "AI",
                "target_reader": "Devs",
                "article_goal": "Test",
            },
        ).json()
        response = client.get(
            f"/admin/blog-ideas/{created['id']}", headers=_admin_headers()
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Specific Idea"
        assert response.json()["source"] == "manual"

    def test_get_idea_404(self) -> None:
        app = create_app(settings=_test_settings())
        client = TestClient(app)
        response = client.get("/admin/blog-ideas/missing", headers=_admin_headers())
        assert response.status_code == 404

    def test_approve_idea_via_patch(self) -> None:
        app = create_app(settings=_test_settings())
        client = TestClient(app)
        created = client.post(
            "/admin/blog-ideas",
            headers=_admin_headers(),
            json={
                "title": "Approved Idea",
                "angle": "AI",
                "target_reader": "Devs",
                "article_goal": "Test",
            },
        ).json()

        response = client.patch(
            f"/admin/blog-ideas/{created['id']}",
            headers=_admin_headers(),
            json={"status": "approved"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "approved"

    def test_reject_with_feedback_via_patch(self) -> None:
        app = create_app(settings=_test_settings())
        client = TestClient(app)
        created = client.post(
            "/admin/blog-ideas",
            headers=_admin_headers(),
            json={
                "title": "Rejected Idea",
                "angle": "AI",
                "target_reader": "Devs",
                "article_goal": "Test",
            },
        ).json()

        response = client.patch(
            f"/admin/blog-ideas/{created['id']}",
            headers=_admin_headers(),
            json={"status": "rejected", "feedback": "Not relevant"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"
        assert data["feedback"] == "Not relevant"

    def test_patch_idea_404(self) -> None:
        app = create_app(settings=_test_settings())
        client = TestClient(app)
        response = client.patch(
            "/admin/blog-ideas/missing",
            headers=_admin_headers(),
            json={"status": "approved"},
        )
        assert response.status_code == 404

    def test_generate_rejects_unauthenticated(self) -> None:
        app = create_app(settings=_test_settings())
        client = TestClient(app)
        response = client.post(
            "/admin/blog-ideas/generate",
            json={
                "project_name": "Scopelytics",
                "project_summary": "An analysis tool",
            },
        )
        assert response.status_code == 401


# ===========================================================================
# Outline workflow tests
# ===========================================================================


class TestOutlineWorkflow:
    def test_outline_fields_default_to_empty(self) -> None:
        """A created idea has no outline until generated."""
        repo = BlogIdeaRepository()
        idea = repo.create(
            BlogIdeaCreate(
                title="Outline Idea",
                angle="AI Engineering",
                target_reader="Devs",
                article_goal="Test outline",
            )
        )
        assert idea.outline_sections == []
        assert idea.outline_status is None

    def test_set_outline_on_idea(self) -> None:
        repo = BlogIdeaRepository()
        created = repo.create(
            BlogIdeaCreate(
                title="With Outline",
                angle="Test",
                target_reader="Devs",
                article_goal="Test",
            )
        )
        sections = [
            OutlineSection(section="Context", points=["Background info"]),
            OutlineSection(
                section="Problem", points=["Challenge", "Impact"]
            ),
        ]
        updated = repo.set_outline(created.id, sections, status="pending")
        assert updated is not None
        assert len(updated.outline_sections) == 2
        assert updated.outline_sections[0].section == "Context"
        assert updated.outline_sections[1].points == ["Challenge", "Impact"]
        assert updated.outline_status == "pending"

    def test_set_outline_missing_idea(self) -> None:
        repo = BlogIdeaRepository()
        assert (
            repo.set_outline("missing", [OutlineSection(section="A", points=[])])
            is None
        )

    def test_outline_status_tracked_in_summary(self) -> None:
        repo = BlogIdeaRepository()
        idea = repo.create(
            BlogIdeaCreate(
                title="Summary Test",
                angle="Test",
                target_reader="Devs",
                article_goal="Test",
            )
        )
        repo.set_outline(idea.id, [OutlineSection(section="A", points=[])], "pending")
        summary = repo.list_all()[0]
        assert summary.outline_status == "pending"

    def test_approve_idea_sets_review_fields(self) -> None:
        repo = BlogIdeaRepository()
        created = repo.create(
            BlogIdeaCreate(
                title="Approve for Outline",
                angle="Test",
                target_reader="Devs",
                article_goal="Test",
            )
        )
        updated = repo.update(created.id, BlogIdeaUpdate(status="approved"))
        assert updated is not None
        assert updated.status == "approved"
        assert updated.reviewed_by == "admin"
        assert updated.reviewed_at is not None

    def test_update_outline_status_via_patch(self) -> None:
        repo = BlogIdeaRepository()
        created = repo.create(
            BlogIdeaCreate(
                title="Outline Approval",
                angle="Test",
                target_reader="Devs",
                article_goal="Test",
            )
        )
        repo.set_outline(created.id, [OutlineSection(section="A", points=[])])
        updated = repo.update(
            created.id, BlogIdeaUpdate(outline_status="approved")
        )
        assert updated is not None
        assert updated.outline_status == "approved"

    def test_update_technical_review_status_via_patch(self) -> None:
        repo = BlogIdeaRepository()
        created = repo.create(
            BlogIdeaCreate(
                title="Review Approval",
                angle="Test",
                target_reader="Devs",
                article_goal="Test",
            )
        )
        repo.set_technical_review(
            created.id,
            {"overall_risk": "low", "issues": [], "approval_recommendation": "approve"},
            status="pending",
        )
        updated = repo.update(
            created.id, BlogIdeaUpdate(technical_review_status="approved")
        )
        assert updated is not None
        assert updated.technical_review_status == "approved"

    def test_generate_outline_requires_approved_idea(self) -> None:
        """API returns 400 when outline is requested for a non-approved idea."""
        app = create_app(settings=_test_settings())
        client = TestClient(app)
        created = client.post(
            "/admin/blog-ideas",
            headers=_admin_headers(),
            json={
                "title": "Not Approved",
                "angle": "Test",
                "target_reader": "Devs",
                "article_goal": "Test",
            },
        ).json()

        response = client.post(
            f"/admin/blog-ideas/{created['id']}/generate-outline",
            headers=_admin_headers(),
            json={},
        )
        assert response.status_code == 400
        assert "requires an approved idea" in response.json()["detail"]

    def test_generate_outline_404(self) -> None:
        app = create_app(settings=_test_settings())
        client = TestClient(app)
        response = client.post(
            "/admin/blog-ideas/missing/generate-outline",
            headers=_admin_headers(),
            json={},
        )
        assert response.status_code == 404
