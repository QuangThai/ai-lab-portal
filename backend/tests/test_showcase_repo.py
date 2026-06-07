"""Tests for the InMemory ShowcaseRepository (showcase.py).

Focuses on CRUD operations, publish/unpublish status transitions, filtering,
and admin operations using the in-memory repository directly.
"""

from datetime import UTC, datetime

from backend.app.showcase import (
    AdminShowcaseDetail,
    AdminShowcaseSummary,
    Showcase,
    ShowcaseCreate,
    ShowcaseDetail,
    ShowcaseSummary,
    ShowcaseUpdate,
    ShowcaseRepository,
)


# ===========================================================================
# Fixtures
# ===========================================================================


def _make_create(
    slug: str = "test-showcase",
    title: str = "Test Showcase",
    hero_summary: str = "A test showcase summary.",
    industry: str | None = "Technology",
    use_case: str | None = "Demo",
    content_markdown: str = "# Test\n\nShowcase content.",
) -> ShowcaseCreate:
    return ShowcaseCreate(
        slug=slug,
        title=title,
        hero_summary=hero_summary,
        industry=industry,
        use_case=use_case,
        content_markdown=content_markdown,
    )


# ===========================================================================
# Construction
# ===========================================================================


class TestShowcaseRepositoryConstruction:
    def test_constructor_uses_default_items(self) -> None:
        """Default constructor loads DEFAULT_SHOWCASES."""
        repo = ShowcaseRepository()
        all_items = repo.list_all()
        # 2 published + 1 draft = 3
        assert len(all_items) == 3

    def test_constructor_with_custom_items(self) -> None:
        """Custom item list replaces defaults."""
        custom = [
            Showcase(
                id="custom_1",
                slug="custom",
                title="Custom",
                hero_summary="Custom item",
                status="draft",
                published_at=None,
                content_markdown="Content.",
            )
        ]
        repo = ShowcaseRepository(items=custom)
        assert len(repo.list_all()) == 1
        assert repo.get_by_id("custom_1") is not None

    def test_constructor_with_empty_items(self) -> None:
        """Explicitly empty list produces an empty repository."""
        repo = ShowcaseRepository(items=[])
        assert repo.list_all() == []


# ===========================================================================
# Read operations
# ===========================================================================


class TestShowcaseRepositoryRead:
    def test_get_by_id_returns_admin_detail(self) -> None:
        repo = ShowcaseRepository()
        item = repo.get_by_id("showcase_001")
        assert item is not None
        assert isinstance(item, AdminShowcaseDetail)
        assert item.title == "Scopelytics"
        assert item.status == "published"

    def test_get_by_id_returns_none_for_missing(self) -> None:
        repo = ShowcaseRepository()
        assert repo.get_by_id("nonexistent") is None

    def test_list_all_returns_admin_summaries(self) -> None:
        repo = ShowcaseRepository()
        items = repo.list_all()
        assert all(isinstance(i, AdminShowcaseSummary) for i in items)
        assert len(items) == 3

    def test_list_all_sorted_by_published_at_desc(self) -> None:
        """Published items sort before drafts (None published_at last)."""
        repo = ShowcaseRepository()
        items = repo.list_all()
        # showcase_001 (Jun 1) before showcase_002 (May 28) before draft
        assert items[0].id == "showcase_001"
        assert items[1].id == "showcase_002"
        assert items[2].id == "showcase_003"

    def test_list_published_filters_by_status(self) -> None:
        repo = ShowcaseRepository()
        published = repo.list_published()
        assert len(published) == 2
        assert all(isinstance(p, ShowcaseSummary) for p in published)
        slugs = {p.slug for p in published}
        assert slugs == {"scopelytics", "ai-interview-system"}

    def test_list_published_returns_empty_when_none_published(self) -> None:
        repo = ShowcaseRepository(items=[])
        assert repo.list_published() == []

    def test_get_published_by_slug_finds_published(self) -> None:
        repo = ShowcaseRepository()
        item = repo.get_published_by_slug("scopelytics")
        assert item is not None
        assert isinstance(item, ShowcaseDetail)
        assert item.content_markdown is not None

    def test_get_published_by_slug_ignores_drafts(self) -> None:
        repo = ShowcaseRepository()
        item = repo.get_published_by_slug("draft-internal-assistant")
        assert item is None

    def test_get_published_by_slug_returns_none_for_missing(self) -> None:
        repo = ShowcaseRepository()
        assert repo.get_published_by_slug("nonexistent") is None


# ===========================================================================
# Create
# ===========================================================================


class TestShowcaseRepositoryCreate:
    def test_create_returns_draft_with_new_id(self) -> None:
        repo = ShowcaseRepository(items=[])
        item = repo.create(_make_create())
        assert item.id.startswith("showcase_")
        assert item.status == "draft"
        assert item.published_at is None
        assert item.title == "Test Showcase"

    def test_create_adds_to_repository(self) -> None:
        repo = ShowcaseRepository(items=[])
        item = repo.create(_make_create())
        assert repo.get_by_id(item.id) is not None

    def test_create_stores_all_fields(self) -> None:
        repo = ShowcaseRepository(items=[])
        item = repo.create(_make_create(
            slug="full-showcase",
            title="Full Showcase",
            hero_summary="A comprehensive showcase.",
            industry="Healthcare",
            use_case="Patient analytics",
            content_markdown="# Full\n\nDetailed content.",
        ))
        assert item.slug == "full-showcase"
        assert item.industry == "Healthcare"
        assert item.use_case == "Patient analytics"

    def test_create_accepts_optional_fields_as_none(self) -> None:
        repo = ShowcaseRepository(items=[])
        item = repo.create(_make_create(industry=None, use_case=None))
        assert item.industry is None
        assert item.use_case is None


# ===========================================================================
# Update
# ===========================================================================


class TestShowcaseRepositoryUpdate:
    def test_update_modifies_fields(self) -> None:
        repo = ShowcaseRepository(items=[])
        item = repo.create(_make_create())
        updated = repo.update(item.id, ShowcaseUpdate(title="Updated Title"))
        assert updated is not None
        assert updated.title == "Updated Title"

    def test_update_partial_only_changes_provided_fields(self) -> None:
        repo = ShowcaseRepository(items=[])
        item = repo.create(_make_create())
        updated = repo.update(item.id, ShowcaseUpdate(hero_summary="New summary."))
        assert updated is not None
        assert updated.title == "Test Showcase"  # unchanged
        assert updated.hero_summary == "New summary."

    def test_update_returns_none_for_missing(self) -> None:
        repo = ShowcaseRepository()
        result = repo.update("nonexistent", ShowcaseUpdate(title="Noop"))
        assert result is None

    def test_update_with_no_fields_changes_nothing(self) -> None:
        repo = ShowcaseRepository(items=[])
        item = repo.create(_make_create())
        updated = repo.update(item.id, ShowcaseUpdate())
        assert updated is not None
        assert updated.title == "Test Showcase"
        assert updated.hero_summary == "A test showcase summary."


# ===========================================================================
# Publish / Unpublish (status transitions)
# ===========================================================================


class TestShowcaseRepositoryStatusTransitions:
    def test_publish_sets_status_and_published_at(self) -> None:
        repo = ShowcaseRepository(items=[])
        item = repo.create(_make_create())
        published = repo.publish(item.id)
        assert published is not None
        assert published.status == "published"
        assert published.published_at is not None

    def test_publish_returns_none_for_missing(self) -> None:
        repo = ShowcaseRepository()
        assert repo.publish("nonexistent") is None

    def test_unpublish_clears_published_at_and_sets_draft(self) -> None:
        repo = ShowcaseRepository(items=[])
        item = repo.create(_make_create())
        repo.publish(item.id)
        unpublished = repo.unpublish(item.id)
        assert unpublished is not None
        assert unpublished.status == "draft"
        assert unpublished.published_at is None

    def test_unpublish_returns_none_for_missing(self) -> None:
        repo = ShowcaseRepository()
        assert repo.unpublish("nonexistent") is None

    def test_publish_updates_in_place(self) -> None:
        """After publish, get_by_id returns updated status."""
        repo = ShowcaseRepository(items=[])
        item = repo.create(_make_create())
        repo.publish(item.id)
        fetched = repo.get_by_id(item.id)
        assert fetched is not None
        assert fetched.status == "published"

    def test_unpublish_updates_in_place(self) -> None:
        """After unpublish, the item is back in draft."""
        repo = ShowcaseRepository(items=[])
        item = repo.create(_make_create())
        repo.publish(item.id)
        repo.unpublish(item.id)
        fetched = repo.get_by_id(item.id)
        assert fetched is not None
        assert fetched.status == "draft"
        assert fetched.published_at is None

    def test_publish_and_unpublish_repeatedly(self) -> None:
        """Publishing and unpublishing can be done multiple times."""
        repo = ShowcaseRepository(items=[])
        item = repo.create(_make_create())
        for _ in range(3):
            item = repo.publish(item.id)
            assert item is not None and item.status == "published"
            item = repo.unpublish(item.id)
            assert item is not None and item.status == "draft"


# ===========================================================================
# Audit events
# ===========================================================================


class TestShowcaseRepositoryAudit:
    def test_record_audit_creates_event(self) -> None:
        repo = ShowcaseRepository()
        event = repo.record_audit(
            actor_user_id="admin_1",
            actor_email="admin@test.com",
            action="showcase.published",
            entity_id="showcase_001",
        )
        assert event.id.startswith("audit_")
        assert event.action == "showcase.published"
        assert event.entity_type == "showcase"
        assert event.entity_id == "showcase_001"
        assert event.actor_user_id == "admin_1"
        assert event.actor_email == "admin@test.com"

    def test_audit_event_has_timestamp(self) -> None:
        repo = ShowcaseRepository()
        event = repo.record_audit("admin_1", "a@b.com", "showcase.created", "s1")
        assert event.created_at is not None
        assert isinstance(event.created_at, datetime)


# ===========================================================================
# Edge cases
# ===========================================================================


class TestShowcaseRepositoryEdgeCases:
    def test_item_not_visible_publicly_when_draft(self) -> None:
        """Draft items are excluded from both list_published and get_published_by_slug."""
        repo = ShowcaseRepository(items=[])
        repo.create(_make_create(slug="draft-only"))
        assert repo.list_published() == []
        assert repo.get_published_by_slug("draft-only") is None

    def test_delete_not_supported(self) -> None:
        """There's no delete method on ShowcaseRepository."""
        repo = ShowcaseRepository()
        assert not hasattr(repo, "delete")

    def test_image_url_in_public_summary(self) -> None:
        """Public summaries include image_url when set."""
        repo = ShowcaseRepository(items=[])
        item = repo.create(_make_create())
        repo.publish(item.id)
        published = repo.list_published()
        assert len(published) == 1
        assert published[0].image_url is None  # default
