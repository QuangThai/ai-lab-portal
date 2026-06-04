"""Tests for US-055 X/Twitter social ingestion spike."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.app.news_crawl import NewsRawItemRepository
from backend.app.news_social_x_ingest import (
    SocialIngestionResult,
    run_due_social_x_sources,
    run_social_x_ingest,
)
from backend.app.news_sources import (
    NewsSource,
    NewsSourceRepository,
)
from backend.app.social_x import (
    FAKE_XQUIK_ROWS,
    FakeXTwitterProvider,
    SocialPostSourceScope,
)


def _make_source(
    source_id: str = "newssrc_social_test",
    enabled: bool = True,
    handle: str = "@OpenAI",
) -> NewsSource:
    now = datetime.now(UTC)
    return NewsSource(
        id=source_id,
        name="Test Social X Source",
        source_type="social_x",
        url_or_identifier=handle,
        description="Test source for US-055.",
        priority="medium",
        crawl_frequency_minutes=60,
        is_enabled=enabled,
        credibility_base_score=0.7,
        created_at=now,
        updated_at=now,
    )


class TestRunSocialXIngest:
    def test_ingest_accepts_relevant_posts(self) -> None:
        """Accepted posts produce raw items."""
        source = _make_source()
        sources = NewsSourceRepository()
        sources._sources = {source.id: source}
        raw_items = NewsRawItemRepository()

        result = run_social_x_ingest(
            source.id,
            sources=sources,
            raw_items=raw_items,
        )

        assert isinstance(result, SocialIngestionResult)
        assert result.source_id == source.id
        assert result.posts_seen == len(FAKE_XQUIK_ROWS)  # 2 fake posts
        assert result.posts_accepted >= 1  # OpenAI post has URLs + AI keywords
        assert result.items_stored >= 1  # at least one URL stored
        assert result.posts_seen == result.posts_accepted + result.posts_rejected

    def test_ingest_nonexistent_source(self) -> None:
        """Missing source raises ValueError."""
        sources = NewsSourceRepository()
        raw_items = NewsRawItemRepository()

        import pytest

        with pytest.raises(ValueError, match="Social source not found"):
            run_social_x_ingest(
                "nonexistent",
                sources=sources,
                raw_items=raw_items,
            )

    def test_ingest_wrong_source_type(self) -> None:
        """Non-social_x source raises ValueError."""
        now = datetime.now(UTC)
        source = NewsSource(
            id="newssrc_rss_test",
            name="Test RSS",
            source_type="rss",
            url_or_identifier="https://example.com/rss",
            priority="medium",
            crawl_frequency_minutes=60,
            is_enabled=True,
            credibility_base_score=0.7,
            created_at=now,
            updated_at=now,
        )
        sources = NewsSourceRepository()
        sources._sources = {source.id: source}
        raw_items = NewsRawItemRepository()

        import pytest

        with pytest.raises(ValueError, match="is not a social_x source"):
            run_social_x_ingest(
                source.id,
                sources=sources,
                raw_items=raw_items,
            )

    def test_ingest_disabled_source(self) -> None:
        """Disabled source raises ValueError."""
        source = _make_source(enabled=False)
        sources = NewsSourceRepository()
        sources._sources = {source.id: source}
        raw_items = NewsRawItemRepository()

        import pytest

        with pytest.raises(ValueError, match="is disabled"):
            run_social_x_ingest(
                source.id,
                sources=sources,
                raw_items=raw_items,
            )

    def test_ingest_touches_last_crawled(self) -> None:
        """After ingestion, last_crawled_at is updated."""
        source = _make_source()
        sources = NewsSourceRepository()
        sources._sources = {source.id: source}
        raw_items = NewsRawItemRepository()

        assert source.last_crawled_at is None
        run_social_x_ingest(source.id, sources=sources, raw_items=raw_items)
        updated = sources.get_by_id(source.id)
        assert updated is not None
        assert updated.last_crawled_at is not None

    def test_ingest_custom_provider(self) -> None:
        """Custom provider rows are used instead of defaults."""
        source = _make_source()
        sources = NewsSourceRepository()
        sources._sources = {source.id: source}
        raw_items = NewsRawItemRepository()
        scope = SocialPostSourceScope(
            provider="fake",
            provider_actor="custom_test",
            source_kind="handle",
            source_value="@test_account",
            crawl_run_id="test_001",
        )
        custom_rows = [
            {
                "id": "test_post_001",
                "text": "New open-source LLM benchmark results https://example.com/benchmark",
                "createdAt": "2026-06-04T12:00:00Z",
                "likeCount": 100,
                "retweetCount": 20,
                "url": "https://x.com/test/status/test_post_001",
                "author": {"username": "test_user", "followers": 5000, "verified": False},
                "entities": {
                    "urls": [
                        {
                            "url": "https://t.co/bench",
                            "expanded_url": "https://example.com/benchmark",
                        }
                    ]
                },
            }
        ]
        provider = FakeXTwitterProvider(rows=custom_rows)

        result = run_social_x_ingest(
            source.id,
            sources=sources,
            raw_items=raw_items,
            provider=provider,
        )

        assert result.posts_seen == 1
        assert result.posts_accepted == 1
        assert result.items_stored == 1


class TestRunDueSocialXSources:
    def test_ingests_due_sources(self) -> None:
        """Due social_x sources are ingested."""
        source = _make_source()
        sources = NewsSourceRepository()
        sources._sources = {source.id: source}
        raw_items = NewsRawItemRepository()

        results = run_due_social_x_sources(
            sources=sources,
            raw_items=raw_items,
        )

        assert len(results) == 1
        assert results[0].posts_seen >= 1

    def test_skips_non_social_sources(self) -> None:
        """Non-social_x sources are skipped."""
        now = datetime.now(UTC)
        rss_source = NewsSource(
            id="newssrc_rss_test",
            name="Test RSS",
            source_type="rss",
            url_or_identifier="https://example.com/rss",
            priority="medium",
            crawl_frequency_minutes=60,
            is_enabled=True,
            credibility_base_score=0.7,
            created_at=now,
            updated_at=now,
        )
        sources = NewsSourceRepository()
        sources._sources = {rss_source.id: rss_source}
        raw_items = NewsRawItemRepository()

        results = run_due_social_x_sources(
            sources=sources,
            raw_items=raw_items,
        )

        assert len(results) == 0

    def test_skips_not_yet_due_sources(self) -> None:
        """Sources crawled recently are skipped."""
        source = _make_source()
        recent = datetime(2099, 1, 1, tzinfo=UTC)  # far in the future
        source.last_crawled_at = recent
        sources = NewsSourceRepository()
        sources._sources = {source.id: source}
        raw_items = NewsRawItemRepository()

        results = run_due_social_x_sources(
            sources=sources,
            raw_items=raw_items,
        )

        assert len(results) == 0
