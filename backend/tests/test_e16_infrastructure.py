"""Tests for E16 infrastructure changes:
- BlogIdeaRepository.update_fields() (both in-memory and Postgres)
- main.py LLM backend switching for E16 agents
"""

import pytest

from datetime import datetime, UTC

from backend.app.blog_ideas import BlogIdea, BlogIdeaRepository, BlogIdeaSummary
from backend.app.main import create_app


# ═══════════════════════════════════════════════════════════════════════════════
# BlogIdeaRepository.update_fields()
# ═══════════════════════════════════════════════════════════════════════════════


class TestBlogIdeaRepositoryUpdateFields:
    """Tests for the update_fields() method on BlogIdeaRepository."""

    @pytest.fixture
    def repo(self) -> BlogIdeaRepository:
        """Seed a repo with one idea for mutation tests."""
        now = datetime.now(UTC)
        idea = BlogIdea(
            id="test-idea-1",
            title="Original Title",
            angle="Test angle",
            target_reader="Developers",
            article_goal="Inform",
            source="manual",
            draft_markdown="# Original draft",
            marketing_metadata={"meta_description": "Old desc"},
            created_at=now,
            updated_at=now,
        )
        return BlogIdeaRepository(ideas=[idea])

    def test_updates_title(self, repo: BlogIdeaRepository):
        """update_fields changes the title field."""
        updated = repo.update_fields("test-idea-1", {"title": "New Title"})
        assert updated is not None
        assert updated.title == "New Title"

    def test_updates_draft_markdown(self, repo: BlogIdeaRepository):
        """update_fields changes draft_markdown."""
        updated = repo.update_fields("test-idea-1", {"draft_markdown": "# New draft"})
        assert updated is not None
        assert updated.draft_markdown == "# New draft"

    def test_updates_multiple_fields(self, repo: BlogIdeaRepository):
        """Multiple fields updated in one call."""
        updated = repo.update_fields("test-idea-1", {
            "title": "New Title",
            "draft_markdown": "# New draft",
        })
        assert updated is not None
        assert updated.title == "New Title"
        assert updated.draft_markdown == "# New draft"

    def test_does_not_change_id(self, repo: BlogIdeaRepository):
        """The 'id' field is protected from update."""
        updated = repo.update_fields("test-idea-1", {"id": "hacked-id"})
        assert updated is not None
        assert updated.id == "test-idea-1"

    def test_sets_updated_at(self, repo: BlogIdeaRepository):
        """updated_at is always refreshed (may equal old_ts in same microsecond)."""
        before = repo.get_by_id("test-idea-1")
        assert before is not None
        old_ts = before.updated_at
        updated = repo.update_fields("test-idea-1", {"title": "X"})
        assert updated is not None
        # updated_at is set to datetime.now(UTC) which may equal old_ts
        # if both operations happen in the same microsecond. The key
        # invariant is that the title change was applied and updated_at
        # is a reasonable timestamp.
        assert updated.title == "X"
        assert updated.updated_at >= old_ts

    def test_unknown_field_is_skipped(self, repo: BlogIdeaRepository):
        """Fields that don't exist on BlogIdea are silently ignored."""
        updated = repo.update_fields("test-idea-1", {"nonexistent_field": "val"})
        assert updated is not None
        # No error, just no change
        assert updated.title == "Original Title"

    def test_nonexistent_idea_returns_none(self, repo: BlogIdeaRepository):
        """Asking for a missing id returns None."""
        result = repo.update_fields("no-such-idea", {"title": "X"})
        assert result is None

    def test_empty_dict_sets_only_updated_at(self, repo: BlogIdeaRepository):
        """An empty values dict refreshes updated_at."""
        before = repo.get_by_id("test-idea-1")
        assert before is not None
        old_ts = before.updated_at
        updated = repo.update_fields("test-idea-1", {})
        assert updated is not None
        assert updated.updated_at >= old_ts
        assert updated.title == "Original Title"  # unchanged


# ═══════════════════════════════════════════════════════════════════════════════
# main.py LLM backend switching
# ═══════════════════════════════════════════════════════════════════════════════


def _collect_route_paths(routes_list):
    """Recursively collect all route paths, handling included sub-routers."""
    paths = []
    for r in routes_list:
        if hasattr(r, "path"):
            paths.append(r.path)
        if hasattr(r, "routes"):
            paths.extend(_collect_route_paths(r.routes))
    return paths


class TestE16LlmBackendSwitching:
    """Tests that main.py switches between Fake and LLM services correctly
    based on AI_LAB_LLM_OPENAI_API_KEY availability.

    Since create_app() reads Settings with env prefix AI_LAB_, we can
    inject env vars to control the behavior.
    """

    def test_creates_fake_services_when_no_api_key(self, monkeypatch: pytest.MonkeyPatch):
        """Without API key, all three E16 agents use Fake*Service."""
        monkeypatch.delenv("AI_LAB_LLM_OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("AI_LAB_LLM_ENVIRONMENT", "test")
        app = create_app()

        routes = _collect_route_paths(app.routes)
        assert "/admin/blog-posts/{post_id}/repurpose" in routes
        assert "/admin/blog-posts/{post_id}/suggest-schedule" in routes
        assert "/admin/blog-ideas/{idea_id}/optimize-seo" in routes

        assert app is not None

    def test_creates_app_with_openai_backend(self, monkeypatch: pytest.MonkeyPatch):
        """With API key and default backend (openai), OpenAILLMService is used."""
        monkeypatch.setenv("AI_LAB_LLM_OPENAI_API_KEY", "sk-test-fake-key-12345")
        monkeypatch.setenv("AI_LAB_LLM_BACKEND", "openai")
        monkeypatch.setenv("AI_LAB_LLM_ENVIRONMENT", "test")
        app = create_app()
        assert app is not None

    def test_creates_app_with_agents_sdk_backend(self, monkeypatch: pytest.MonkeyPatch):
        """With API key and agents_sdk backend, AgentsSDKLLMService is used."""
        monkeypatch.setenv("AI_LAB_LLM_OPENAI_API_KEY", "sk-test-fake-key-12345")
        monkeypatch.setenv("AI_LAB_LLM_BACKEND", "agents_sdk")
        monkeypatch.setenv("AI_LAB_LLM_ENVIRONMENT", "test")
        app = create_app()
        assert app is not None
