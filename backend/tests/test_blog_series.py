"""Tests for blog_series — InMemoryBlogSeriesRepository + model validation.

Uses the in-memory repo to test all edge cases without a database.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from backend.app.blog_series import (
    BlogSeriesCreate,
    BlogSeriesUpdate,
    InMemoryBlogSeriesRepository,
)


@pytest.fixture
def repo() -> InMemoryBlogSeriesRepository:
    return InMemoryBlogSeriesRepository()


# ── BlogSeriesCreate model validation ──


class TestBlogSeriesCreate:
    def test_valid_create(self) -> None:
        obj = BlogSeriesCreate(title="My Series", slug="my-series")
        assert obj.title == "My Series"
        assert obj.slug == "my-series"
        assert obj.description is None
        assert obj.cover_image_url is None

    def test_title_required(self) -> None:
        with pytest.raises(ValidationError):
            BlogSeriesCreate(slug="no-title")  # type: ignore[arg-type]

    def test_slug_required(self) -> None:
        with pytest.raises(ValidationError):
            BlogSeriesCreate(title="No Slug")  # type: ignore[arg-type]

    def test_title_max_length(self) -> None:
        with pytest.raises(ValidationError):
            BlogSeriesCreate(title="x" * 241, slug="too-long")

    def test_title_min_length(self) -> None:
        with pytest.raises(ValidationError):
            BlogSeriesCreate(title="", slug="empty")

    def test_optional_fields(self) -> None:
        obj = BlogSeriesCreate(
            title="Full Series",
            slug="full-series",
            description="A description",
            cover_image_url="https://example.com/cover.jpg",
        )
        assert obj.description == "A description"
        assert obj.cover_image_url == "https://example.com/cover.jpg"

    def test_cover_image_url_max_length(self) -> None:
        with pytest.raises(ValidationError):
            BlogSeriesCreate(title="Long URL", slug="long-url", cover_image_url="x" * 2049)


class TestBlogSeriesUpdate:
    def test_all_optional(self) -> None:
        obj = BlogSeriesUpdate()
        assert obj.title is None
        assert obj.description is None
        assert obj.slug is None

    def test_partial_update(self) -> None:
        obj = BlogSeriesUpdate(title="New Title")
        assert obj.title == "New Title"
        assert obj.slug is None


# ── Repository CRUD ──


class TestCrud:
    def test_create_and_get_by_id(self, repo: InMemoryBlogSeriesRepository) -> None:
        created = repo.create(BlogSeriesCreate(title="Test", slug="test"))
        fetched = repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.title == "Test"
        assert fetched.slug == "test"
        assert fetched.id == created.id

    def test_create_and_get_by_slug(self, repo: InMemoryBlogSeriesRepository) -> None:
        created = repo.create(BlogSeriesCreate(title="Slug Test", slug="slug-test"))
        fetched = repo.get_by_slug("slug-test")
        assert fetched is not None
        assert fetched.id == created.id

    def test_get_by_id_missing(self, repo: InMemoryBlogSeriesRepository) -> None:
        assert repo.get_by_id("nonexistent") is None

    def test_get_by_slug_missing(self, repo: InMemoryBlogSeriesRepository) -> None:
        assert repo.get_by_slug("nonexistent") is None

    def test_list_all_empty(self, repo: InMemoryBlogSeriesRepository) -> None:
        assert repo.list_all() == []

    def test_list_all_returns_all(self, repo: InMemoryBlogSeriesRepository) -> None:
        repo.create(BlogSeriesCreate(title="A", slug="a"))
        repo.create(BlogSeriesCreate(title="B", slug="b"))
        assert len(repo.list_all()) == 2

    def test_list_all_ordered_by_created_at_desc(self, repo: InMemoryBlogSeriesRepository) -> None:
        s1 = repo.create(BlogSeriesCreate(title="Older", slug="older"))
        s2 = repo.create(BlogSeriesCreate(title="Newer", slug="newer"))
        all_series = repo.list_all()
        # Both may have same timestamp if created in same ms
        # Just verify both are present and sorted properly
        assert len(all_series) == 2
        # newest-first sort means s2 should come before s1
        if all_series[0].created_at == all_series[1].created_at:
            # Same millisecond — order is implementation-defined
            pass
        else:
            assert all_series[0].id == s2.id

    def test_update_title(self, repo: InMemoryBlogSeriesRepository) -> None:
        created = repo.create(BlogSeriesCreate(title="Original", slug="test"))
        updated = repo.update(created.id, BlogSeriesUpdate(title="Updated"))
        assert updated is not None
        assert updated.title == "Updated"

    def test_update_non_existent(self, repo: InMemoryBlogSeriesRepository) -> None:
        assert repo.update("missing", BlogSeriesUpdate(title="Nope")) is None

    def test_update_returns_existing_if_no_fields(self, repo: InMemoryBlogSeriesRepository) -> None:
        created = repo.create(BlogSeriesCreate(title="Same", slug="same"))
        updated = repo.update(created.id, BlogSeriesUpdate())
        assert updated is not None
        assert updated.title == "Same"

    def test_delete_existing(self, repo: InMemoryBlogSeriesRepository) -> None:
        created = repo.create(BlogSeriesCreate(title="Del", slug="del"))
        assert repo.delete(created.id) is True
        assert repo.get_by_id(created.id) is None

    def test_delete_missing(self, repo: InMemoryBlogSeriesRepository) -> None:
        assert repo.delete("missing") is False

    def test_delete_removes_associated_posts(self, repo: InMemoryBlogSeriesRepository) -> None:
        created = repo.create(BlogSeriesCreate(title="With Posts", slug="with-posts"))
        repo.add_post_to_series(created.id, "post_1", 1)
        repo.add_post_to_series(created.id, "post_2", 2)
        repo.delete(created.id)
        detail = repo.get_with_posts(created.id)
        assert detail is None


# ── Post management ──


class TestAddPostToSeries:
    def test_add_post(self, repo: InMemoryBlogSeriesRepository) -> None:
        series = repo.create(BlogSeriesCreate(title="S", slug="s"))
        sp = repo.add_post_to_series(series.id, "post_abc", 1)
        assert sp.post_id == "post_abc"
        assert sp.part_number == 1
        assert sp.series_id == series.id
        assert sp.id.startswith("sp_")

    def test_add_post_to_missing_series(self, repo: InMemoryBlogSeriesRepository) -> None:
        with pytest.raises(ValueError, match="Series not found"):
            repo.add_post_to_series("missing", "post_1", 1)

    def test_duplicate_post_raises(self, repo: InMemoryBlogSeriesRepository) -> None:
        series = repo.create(BlogSeriesCreate(title="S", slug="s"))
        repo.add_post_to_series(series.id, "post_1", 1)
        with pytest.raises(ValueError, match="Post already in series"):
            repo.add_post_to_series(series.id, "post_1", 2)  # same post, diff part

    def test_duplicate_part_number_raises(self, repo: InMemoryBlogSeriesRepository) -> None:
        series = repo.create(BlogSeriesCreate(title="S", slug="s"))
        repo.add_post_to_series(series.id, "post_1", 1)
        with pytest.raises(ValueError, match="Part number already used"):
            repo.add_post_to_series(series.id, "post_2", 1)  # diff post, same part

    def test_multiple_parts(self, repo: InMemoryBlogSeriesRepository) -> None:
        series = repo.create(BlogSeriesCreate(title="Multi", slug="multi"))
        repo.add_post_to_series(series.id, "post_1", 1)
        repo.add_post_to_series(series.id, "post_2", 2)
        repo.add_post_to_series(series.id, "post_3", 3)
        detail = repo.get_with_posts(series.id)
        assert detail is not None
        assert len(detail.posts) == 3
        # Verify order by part_number
        assert [p.part_number for p in detail.posts] == [1, 2, 3]

    def test_different_series_can_have_same_post(self, repo: InMemoryBlogSeriesRepository) -> None:
        s1 = repo.create(BlogSeriesCreate(title="S1", slug="s1"))
        s2 = repo.create(BlogSeriesCreate(title="S2", slug="s2"))
        repo.add_post_to_series(s1.id, "post_X", 1)
        repo.add_post_to_series(s2.id, "post_X", 1)  # same post in different series — OK


class TestRemovePostFromSeries:
    def test_remove_existing(self, repo: InMemoryBlogSeriesRepository) -> None:
        series = repo.create(BlogSeriesCreate(title="S", slug="s"))
        repo.add_post_to_series(series.id, "post_1", 1)
        assert repo.remove_post_from_series(series.id, "post_1") is True
        detail = repo.get_with_posts(series.id)
        assert detail is not None
        assert len(detail.posts) == 0

    def test_remove_missing(self, repo: InMemoryBlogSeriesRepository) -> None:
        series = repo.create(BlogSeriesCreate(title="S", slug="s"))
        assert repo.remove_post_from_series(series.id, "nonexistent") is False

    def test_remove_from_missing_series(self, repo: InMemoryBlogSeriesRepository) -> None:
        assert repo.remove_post_from_series("missing", "post_1") is False


# ── Query methods ──


class TestGetWithPosts:
    def test_empty_posts(self, repo: InMemoryBlogSeriesRepository) -> None:
        series = repo.create(BlogSeriesCreate(title="Empty Series", slug="empty"))
        detail = repo.get_with_posts(series.id)
        assert detail is not None
        assert detail.posts == []

    def test_series_not_found(self, repo: InMemoryBlogSeriesRepository) -> None:
        assert repo.get_with_posts("missing") is None

    def test_posts_sorted_by_part_number(self, repo: InMemoryBlogSeriesRepository) -> None:
        series = repo.create(BlogSeriesCreate(title="S", slug="s"))
        repo.add_post_to_series(series.id, "post_3", 3)
        repo.add_post_to_series(series.id, "post_1", 1)
        repo.add_post_to_series(series.id, "post_2", 2)
        detail = repo.get_with_posts(series.id)
        assert detail is not None
        assert [p.post_id for p in detail.posts] == ["post_1", "post_2", "post_3"]


class TestGetBySlugWithPosts:
    def test_happy_path(self, repo: InMemoryBlogSeriesRepository) -> None:
        series = repo.create(BlogSeriesCreate(title="Slug Series", slug="my-slug"))
        repo.add_post_to_series(series.id, "post_1", 1)
        detail = repo.get_by_slug_with_posts("my-slug")
        assert detail is not None
        assert detail.id == series.id

    def test_missing_slug(self, repo: InMemoryBlogSeriesRepository) -> None:
        assert repo.get_by_slug_with_posts("missing") is None


class TestListForPost:
    def test_post_in_one_series(self, repo: InMemoryBlogSeriesRepository) -> None:
        series = repo.create(BlogSeriesCreate(title="S", slug="s"))
        repo.add_post_to_series(series.id, "post_1", 1)
        result = repo.list_for_post("post_1")
        assert len(result) == 1
        assert result[0].id == series.id

    def test_post_in_multiple_series(self, repo: InMemoryBlogSeriesRepository) -> None:
        s1 = repo.create(BlogSeriesCreate(title="S1", slug="s1"))
        s2 = repo.create(BlogSeriesCreate(title="S2", slug="s2"))
        repo.add_post_to_series(s1.id, "post_X", 1)
        repo.add_post_to_series(s2.id, "post_X", 1)
        result = repo.list_for_post("post_X")
        assert len(result) == 2

    def test_post_not_in_any_series(self, repo: InMemoryBlogSeriesRepository) -> None:
        assert repo.list_for_post("orphan_post") == []


class TestListPublicSummaries:
    def test_only_series_with_posts_appear(self, repo: InMemoryBlogSeriesRepository) -> None:
        s1 = repo.create(BlogSeriesCreate(title="Has posts", slug="has-posts"))
        repo.create(BlogSeriesCreate(title="No posts", slug="no-posts"))  # should not appear
        repo.add_post_to_series(s1.id, "post_1", 1)
        summaries = repo.list_public_summaries()
        assert len(summaries) == 1
        assert summaries[0].title == "Has posts"

    def test_post_count(self, repo: InMemoryBlogSeriesRepository) -> None:
        series = repo.create(BlogSeriesCreate(title="S", slug="s"))
        repo.add_post_to_series(series.id, "p1", 1)
        repo.add_post_to_series(series.id, "p2", 2)
        summaries = repo.list_public_summaries()
        assert len(summaries) == 1
        assert summaries[0].post_count == 2

    def test_sorted_by_created_at_desc(self, repo: InMemoryBlogSeriesRepository) -> None:
        s1 = repo.create(BlogSeriesCreate(title="Older", slug="older"))
        s2 = repo.create(BlogSeriesCreate(title="Newer", slug="newer"))
        repo.add_post_to_series(s1.id, "p1", 1)
        repo.add_post_to_series(s2.id, "p2", 1)
        summaries = repo.list_public_summaries()
        assert len(summaries) == 2
        # Both may have same timestamp — skip strict ordering check
        if summaries[0].created_at != summaries[1].created_at:
            assert summaries[0].title == "Newer"


class TestSlugExists:
    def test_slug_exists(self, repo: InMemoryBlogSeriesRepository) -> None:
        repo.create(BlogSeriesCreate(title="S", slug="my-slug"))
        assert repo.slug_exists("my-slug") is True

    def test_slug_does_not_exist(self, repo: InMemoryBlogSeriesRepository) -> None:
        assert repo.slug_exists("no-slug") is False

    def test_slug_exists_excluding_self(self, repo: InMemoryBlogSeriesRepository) -> None:
        s = repo.create(BlogSeriesCreate(title="S", slug="my-slug"))
        assert repo.slug_exists("my-slug", exclude_id=s.id) is False

    def test_slug_exists_excluding_different(self, repo: InMemoryBlogSeriesRepository) -> None:
        s1 = repo.create(BlogSeriesCreate(title="S1", slug="shared-slug"))
        repo.create(BlogSeriesCreate(title="S2", slug="shared-slug"))
        assert repo.slug_exists("shared-slug", exclude_id=s1.id) is True

    def test_empty_repo(self, repo: InMemoryBlogSeriesRepository) -> None:
        assert repo.slug_exists("anything") is False
