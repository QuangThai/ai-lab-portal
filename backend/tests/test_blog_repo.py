"""Tests for the InMemory BlogRepository (blog.py).

Focuses on CRUD operations, status transitions, pagination/filtering, slug
deduplication, and audit events using the in-memory repository directly.
"""

from datetime import UTC, datetime

from backend.app.blog import (
    AdminBlogPostDetail,
    AdminBlogPostSummary,
    BlogPost,
    BlogPostCreate,
    BlogPostSummary,
    BlogPostUpdate,
    BlogRepository,
)


# ===========================================================================
# Fixtures
# ===========================================================================


def _make_create(
    slug: str = "test-post",
    title: str = "Test Post",
    excerpt: str = "A test blog post.",
    author_name: str = "Tester",
    content_markdown: str = "# Test\n\nBody content.",
) -> BlogPostCreate:
    return BlogPostCreate(
        slug=slug,
        title=title,
        excerpt=excerpt,
        author_name=author_name,
        content_markdown=content_markdown,
    )


# ===========================================================================
# Construction
# ===========================================================================


class TestBlogRepositoryConstruction:
    def test_constructor_uses_default_posts(self) -> None:
        """Default constructor loads DEFAULT_BLOG_POSTS."""
        repo = BlogRepository()
        all_posts = repo.list_all()
        assert len(all_posts) == 2

    def test_constructor_with_custom_posts(self) -> None:
        """Custom post list replaces defaults."""
        custom = [
            BlogPost(
                id="custom_1",
                slug="custom",
                title="Custom",
                excerpt="Custom post",
                author_name="Me",
                status="draft",
                published_at=None,
                content_markdown="Custom content.",
            )
        ]
        repo = BlogRepository(posts=custom)
        assert len(repo.list_all()) == 1
        assert repo.get_by_id("custom_1") is not None

    def test_constructor_with_empty_posts(self) -> None:
        """Explicitly empty list produces an empty repository."""
        repo = BlogRepository(posts=[])
        assert repo.list_all() == []


# ===========================================================================
# Read operations
# ===========================================================================


class TestBlogRepositoryRead:
    def test_get_by_id_returns_admin_detail(self) -> None:
        repo = BlogRepository()
        post = repo.get_by_id("post_001")
        assert post is not None
        assert isinstance(post, AdminBlogPostDetail)
        assert post.title == "Building an AI Lab with Human Review at the Center"
        assert post.status == "published"

    def test_get_by_id_returns_none_for_missing(self) -> None:
        repo = BlogRepository()
        assert repo.get_by_id("nonexistent") is None

    def test_get_by_slug_finds_post(self) -> None:
        repo = BlogRepository()
        post = repo.get_by_slug("building-an-ai-lab-with-human-review")
        assert post is not None
        assert post.id == "post_001"

    def test_get_by_slug_returns_none_for_missing(self) -> None:
        repo = BlogRepository()
        assert repo.get_by_slug("nonexistent-slug") is None

    def test_list_all_returns_admin_summaries(self) -> None:
        repo = BlogRepository()
        posts = repo.list_all()
        assert all(isinstance(p, AdminBlogPostSummary) for p in posts)
        assert len(posts) == 2

    def test_list_all_sorted_by_published_at_desc(self) -> None:
        """Published posts sort before drafts (None published_at last)."""
        repo = BlogRepository()
        posts = repo.list_all()
        # post_001 (published) should come before post_002 (draft)
        assert posts[0].id == "post_001"
        assert posts[1].id == "post_002"

    def test_list_published_filters_by_status(self) -> None:
        repo = BlogRepository()
        published = repo.list_published()
        assert len(published) == 1
        assert all(isinstance(p, BlogPostSummary) for p in published)
        assert published[0].slug == "building-an-ai-lab-with-human-review"

    def test_list_published_with_post_ids_filter(self) -> None:
        repo = BlogRepository()
        result = repo.list_published(post_ids={"post_001"})
        assert len(result) == 1
        result = repo.list_published(post_ids={"post_999"})
        assert len(result) == 0

    def test_list_published_with_author_user_ids_filter(self) -> None:
        repo = BlogRepository()
        # The default posts have author_user_id=None, so filter on a non-matching ID
        result = repo.list_published(author_user_ids={"author_999"})
        assert len(result) == 0

    def test_list_published_with_search_on_title(self) -> None:
        repo = BlogRepository()
        result = repo.list_published(q="human")
        assert len(result) == 1
        assert result[0].slug == "building-an-ai-lab-with-human-review"

    def test_list_published_with_search_on_excerpt(self) -> None:
        repo = BlogRepository()
        result = repo.list_published(q="evidence")
        assert len(result) == 1

    def test_list_published_with_search_no_matches(self) -> None:
        repo = BlogRepository()
        result = repo.list_published(q="nonexistent content")
        assert result == []

    def test_get_published_by_slug_finds_published(self) -> None:
        repo = BlogRepository()
        post = repo.get_published_by_slug("building-an-ai-lab-with-human-review")
        assert post is not None
        assert post.content_markdown is not None

    def test_get_published_by_slug_ignores_drafts(self) -> None:
        repo = BlogRepository()
        post = repo.get_published_by_slug("draft-provider-scorecards")
        assert post is None

    def test_get_published_by_slug_returns_none_for_missing(self) -> None:
        repo = BlogRepository()
        assert repo.get_published_by_slug("nonexistent") is None


# ===========================================================================
# Create
# ===========================================================================


class TestBlogRepositoryCreate:
    def test_create_returns_draft_with_new_id(self) -> None:
        repo = BlogRepository(posts=[])
        post = repo.create(_make_create())
        assert post.id.startswith("post_")
        assert post.status == "draft"
        assert post.published_at is None
        assert post.title == "Test Post"

    def test_create_adds_to_repository(self) -> None:
        repo = BlogRepository(posts=[])
        post = repo.create(_make_create())
        assert repo.get_by_id(post.id) is not None

    def test_create_deduplicates_slug(self) -> None:
        repo = BlogRepository(posts=[])
        repo.create(_make_create(slug="my-post"))
        second = repo.create(_make_create(slug="my-post"))
        assert second.slug == "my-post-2"

    def test_create_deduplicates_with_multiple_collisions(self) -> None:
        repo = BlogRepository(posts=[])
        repo.create(_make_create(slug="my-post"))
        repo.create(_make_create(slug="my-post"))
        third = repo.create(_make_create(slug="my-post"))
        assert third.slug == "my-post-3"


# ===========================================================================
# Update
# ===========================================================================


class TestBlogRepositoryUpdate:
    def test_update_modifies_fields(self) -> None:
        repo = BlogRepository(posts=[])
        post = repo.create(_make_create())
        updated = repo.update(post.id, BlogPostUpdate(title="Updated Title"))
        assert updated is not None
        assert updated.title == "Updated Title"

    def test_update_partial_only_changes_provided_fields(self) -> None:
        repo = BlogRepository(posts=[])
        post = repo.create(_make_create())
        updated = repo.update(post.id, BlogPostUpdate(excerpt="New excerpt."))
        assert updated is not None
        assert updated.title == "Test Post"  # unchanged
        assert updated.excerpt == "New excerpt."

    def test_update_returns_none_for_missing(self) -> None:
        repo = BlogRepository()
        result = repo.update("nonexistent", BlogPostUpdate(title="Noop"))
        assert result is None


# ===========================================================================
# Publish / Unpublish (status transitions)
# ===========================================================================


class TestBlogRepositoryStatusTransitions:
    def test_publish_sets_status_and_published_at(self) -> None:
        repo = BlogRepository(posts=[])
        post = repo.create(_make_create())
        published = repo.publish(post.id)
        assert published is not None
        assert published.status == "published"
        assert published.published_at is not None

    def test_publish_returns_none_for_missing(self) -> None:
        repo = BlogRepository()
        assert repo.publish("nonexistent") is None

    def test_unpublish_clears_published_at_and_sets_draft(self) -> None:
        repo = BlogRepository(posts=[])
        post = repo.create(_make_create())
        repo.publish(post.id)
        unpublished = repo.unpublish(post.id)
        assert unpublished is not None
        assert unpublished.status == "draft"
        assert unpublished.published_at is None

    def test_unpublish_returns_none_for_missing(self) -> None:
        repo = BlogRepository()
        assert repo.unpublish("nonexistent") is None

    def test_publish_updates_in_place(self) -> None:
        """After publish, get_by_id returns updated status."""
        repo = BlogRepository(posts=[])
        post = repo.create(_make_create())
        repo.publish(post.id)
        fetched = repo.get_by_id(post.id)
        assert fetched is not None
        assert fetched.status == "published"

    def test_unpublish_updates_in_place(self) -> None:
        """After unpublish, the post is back in draft."""
        repo = BlogRepository(posts=[])
        post = repo.create(_make_create())
        repo.publish(post.id)
        repo.unpublish(post.id)
        fetched = repo.get_by_id(post.id)
        assert fetched is not None
        assert fetched.status == "draft"
        assert fetched.published_at is None


# ===========================================================================
# Audit events
# ===========================================================================


class TestBlogRepositoryAudit:
    def test_record_audit_creates_event(self) -> None:
        repo = BlogRepository()
        event = repo.record_audit(
            actor_user_id="admin_1",
            actor_email="admin@test.com",
            action="blog_post.published",
            entity_id="post_001",
        )
        assert event.id.startswith("audit_")
        assert event.action == "blog_post.published"
        assert event.entity_type == "blog_post"
        assert event.entity_id == "post_001"
        assert event.actor_user_id == "admin_1"

    def test_record_audit_adds_to_list(self) -> None:
        repo = BlogRepository()
        repo.record_audit("admin_1", "admin@test.com", "blog_post.created", "post_001")
        events = repo.list_audit_events()
        assert len(events) == 1

    def test_list_audit_events_returns_all(self) -> None:
        repo = BlogRepository()
        repo.record_audit("admin_1", "a@b.com", "create", "p1")
        repo.record_audit("admin_2", "c@d.com", "publish", "p1")
        events = repo.list_audit_events()
        assert len(events) == 2

    def test_audit_event_has_timestamp(self) -> None:
        repo = BlogRepository()
        event = repo.record_audit("admin_1", "a@b.com", "action", "p1")
        assert event.created_at is not None
        assert isinstance(event.created_at, datetime)


# ===========================================================================
# Edge cases and integration
# ===========================================================================


class TestBlogRepositoryEdgeCases:
    def test_list_published_with_empty_post_ids_returns_empty(self) -> None:
        repo = BlogRepository()
        result = repo.list_published(post_ids=set())
        assert result == []

    def test_list_published_with_empty_author_user_ids_returns_empty(self) -> None:
        repo = BlogRepository()
        result = repo.list_published(author_user_ids=set())
        assert result == []

    def test_update_with_no_fields_changes_nothing(self) -> None:
        repo = BlogRepository(posts=[])
        post = repo.create(_make_create())
        updated = repo.update(post.id, BlogPostUpdate())
        assert updated is not None
        assert updated.title == "Test Post"
        assert updated.excerpt == "A test blog post."

    def test_create_stores_image_url_and_author_user_id(self) -> None:
        repo = BlogRepository(posts=[])
        req = _make_create()
        req.image_url = "https://example.com/image.png"
        req.author_user_id = "author_001"
        post = repo.create(req)
        assert post.image_url == "https://example.com/image.png"
        assert post.author_user_id == "author_001"
        fetched = repo.get_by_id(post.id)
        assert fetched is not None
        assert fetched.image_url == "https://example.com/image.png"
        assert fetched.author_user_id == "author_001"

    def test_list_published_filters_by_author_user_id_match(self) -> None:
        repo = BlogRepository(posts=[])
        req = _make_create(slug="by-author")
        req.author_user_id = "author_001"
        post = repo.create(req)
        repo.publish(post.id)
        result = repo.list_published(author_user_ids={"author_001"})
        assert len(result) == 1
        assert result[0].slug == "by-author"
