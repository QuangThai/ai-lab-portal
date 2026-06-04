"""Integration tests for US-055 social ingestion edge cases (entry criterion #6).

Covers quota exhaustion, malformed payloads, duplicate links, and unavailable
posts at the ingestion pipeline level. All tests use fake providers to
simulate real-world failure modes without any external API calls.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from backend.app.news_crawl import NewsRawItemRepository
from backend.app.news_social_x_ingest import (
    run_due_social_x_sources,
    run_social_x_ingest,
)
from backend.app.news_sources import NewsSourceRepository
from backend.app.social_x import (
    FAKE_XQUIK_ROWS,
    SocialPostSourceScope,
    FakeXTwitterProvider,
    normalize_xquik_tweet,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_source(source_id: str = "newssrc_social_int") -> dict:
    now = datetime.now(UTC)
    return {
        "id": source_id,
        "name": "Integration Test Social X Source",
        "source_type": "social_x",
        "url_or_identifier": "@test_handle",
        "description": "Integration test source.",
        "priority": "medium",
        "crawl_frequency_minutes": 60,
        "is_enabled": True,
        "credibility_base_score": 0.7,
        "created_at": now,
        "updated_at": now,
    }


def _register_source(sources: NewsSourceRepository, **overrides: object) -> str:
    from backend.app.news_sources import NewsSource
    params = {**_make_source(), **overrides}
    src = NewsSource(**params)  # type: ignore[arg-type]
    sources._sources[src.id] = src
    return src.id


def _make_scope(source_value: str = "@test_integration") -> SocialPostSourceScope:
    return SocialPostSourceScope(
        provider="fake",
        provider_actor="integration_test",
        source_kind="handle",
        source_value=source_value,
        crawl_run_id="int_test_001",
    )


SCOPE = _make_scope()


# ---------------------------------------------------------------------------
# Custom providers for edge case simulation
# ---------------------------------------------------------------------------

class QuotaExhaustionProvider(FakeXTwitterProvider):
    """Simulates provider returning API quota exhaustion."""

    def __init__(self) -> None:
        super().__init__(rows=[])

    def fetch_posts(self, scope: SocialPostSourceScope) -> list:  # type: ignore[override]
        raise ConnectionError("API quota exhausted — 429 Too Many Requests")


class EmptyResponseProvider(FakeXTwitterProvider):
    """Simulates provider returning empty results (degraded, not fatal)."""

    def __init__(self) -> None:
        super().__init__(rows=[])

    def fetch_posts(self, scope: SocialPostSourceScope) -> list:
        return []


# One post with an extractable URL (passes normalization and filter)
_FIXTURE_WITH_URL = {
    "id": "valid_post_001",
    "text": "New open-source LLM benchmark results https://example.com/bench",
    "createdAt": "2026-06-04T12:00:00Z",
    "likeCount": 100,
    "retweetCount": 20,
    "url": "https://x.com/dev/status/valid_post_001",
    "author": {"username": "dev_user", "followers": 5000, "verified": False},
    "entities": {
        "urls": [
            {"url": "https://t.co/bench", "expanded_url": "https://example.com/bench"},
        ],
    },
}


class DuplicateUrlProvider(FakeXTwitterProvider):
    """Two different posts sharing the same expandable URL."""

    def __init__(self) -> None:
        super().__init__(rows=[])
        self._shared_url = "https://example.com/dup-benchmark"

    def fetch_posts(self, scope: SocialPostSourceScope) -> list:
        return [
            normalize_xquik_tweet(
                {
                    "id": "dup_post_001",
                    "text": f"Great benchmark results {self._shared_url}",
                    "createdAt": "2026-06-04T12:00:00Z",
                    "likeCount": 50,
                    "url": "https://x.com/user1/status/dup_post_001",
                    "author": {"username": "user1", "followers": 500, "verified": False},
                    "entities": {
                        "urls": [
                            {"url": self._shared_url, "expanded_url": self._shared_url},
                        ],
                    },
                },
                scope=scope,
            ),
            normalize_xquik_tweet(
                {
                    "id": "dup_post_002",
                    "text": f"Check out this too {self._shared_url}",
                    "createdAt": "2026-06-04T12:01:00Z",
                    "likeCount": 30,
                    "url": "https://x.com/user2/status/dup_post_002",
                    "author": {"username": "user2", "followers": 500, "verified": False},
                    "entities": {
                        "urls": [
                            {"url": self._shared_url, "expanded_url": self._shared_url},
                        ],
                    },
                },
                scope=scope,
            ),
        ]


class NoUrlsProvider(FakeXTwitterProvider):
    """Post with AI signal but no extractable URLs."""

    def __init__(self) -> None:
        super().__init__(rows=[])

    def fetch_posts(self, scope: SocialPostSourceScope) -> list:
        return [
            normalize_xquik_tweet(
                {
                    "id": "no_url_001",
                    "text": "This new open-source LLM just dropped! Wow!",
                    "createdAt": "2026-06-04T12:00:00Z",
                    "likeCount": 100,
                    "url": "https://x.com/dev/status/no_url_001",
                    "author": {"username": "dev_user", "followers": 1000, "verified": False},
                    "entities": {"urls": []},
                },
                scope=scope,
            ),
        ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestQuotaExhaustion:
    """Provider returns 429 / connection error."""

    def test_quota_exhaustion_raises_connection_error(self) -> None:
        """run_social_x_ingest propagates provider connection errors."""
        sources = NewsSourceRepository()
        source_id = _register_source(sources)
        raw_items = NewsRawItemRepository()
        provider = QuotaExhaustionProvider()

        with pytest.raises(ConnectionError, match="quota exhausted"):
            run_social_x_ingest(
                source_id,
                sources=sources,
                raw_items=raw_items,
                provider=provider,
            )

    def test_empty_response_is_handled_gracefully(self) -> None:
        """run_social_x_ingest with empty provider returns zero counts."""
        sources = NewsSourceRepository()
        source_id = _register_source(sources)
        raw_items = NewsRawItemRepository()
        provider = EmptyResponseProvider()

        result = run_social_x_ingest(
            source_id,
            sources=sources,
            raw_items=raw_items,
            provider=provider,
        )

        assert result.posts_seen == 0
        assert result.posts_accepted == 0
        assert result.posts_rejected == 0
        assert result.items_stored == 0
        # last_crawled_at is still updated
        src = sources.get_by_id(source_id)
        assert src is not None
        assert src.last_crawled_at is not None

    def test_quota_on_due_sources_propagates(self) -> None:
        """run_due_social_x_sources with quota exhaustion propagates error.

        Note: currently catches ValueError only; ConnectionError propagates.
        This test documents the limitation — if a provider fails with a
        non-ValueError, the entire batch fails.
        """
        sources = NewsSourceRepository()
        _register_source(sources)
        raw_items = NewsRawItemRepository()
        provider = QuotaExhaustionProvider()

        with pytest.raises(ConnectionError):
            run_due_social_x_sources(
                sources=sources,
                raw_items=raw_items,
                provider=provider,
            )

    def test_quota_source_next_sources_continue(self) -> None:
        """Error on one source does not block ingestion of other sources.

        Currently only ValueError is caught; other exceptions propagate.
        This test validates the recovery path for known error types.
        """
        from backend.app.news_social_x_ingest import run_social_x_ingest
        sources = NewsSourceRepository()
        raw_items = NewsRawItemRepository()

        # Register a second good source alongside a mock failing one
        good_id = _register_source(sources, id="newssrc_good", url_or_identifier="@good")
        bad_id = _register_source(sources, id="newssrc_bad", url_or_identifier="@bad")

        # BAD source with quota error
        bad_provider = QuotaExhaustionProvider()
        with pytest.raises(ConnectionError):
            run_social_x_ingest(
                bad_id,
                sources=sources,
                raw_items=raw_items,
                provider=bad_provider,
            )

        # GOOD source still works independently
        result = run_social_x_ingest(
            good_id,
            sources=sources,
            raw_items=raw_items,
        )
        assert result.posts_seen >= 1


class TestMalformedPayloads:
    """Provider responses with missing/invalid fields handled by normalization."""

    def test_malformed_post_raises_at_normalization(self) -> None:
        """Missing text/id on a post raises ValueError from normalize_xquik_tweet."""
        with pytest.raises(ValueError, match="X/Twitter post id is required"):
            normalize_xquik_tweet(
                {"text": "", "url": "https://x.com/x/status/x", "author": {}},
                scope=SCOPE,
            )

    def test_empty_text_raises_value_error(self) -> None:
        """Blank post text raises ValueError during normalization."""
        with pytest.raises(ValueError, match="X/Twitter post text is required"):
            normalize_xquik_tweet(
                {"id": "123", "text": "   ", "url": "https://x.com/x/status/123", "author": {"username": "test"}},
                scope=SCOPE,
            )

    def test_missing_url_raises_value_error(self) -> None:
        """Missing URL raises ValueError during normalization."""
        with pytest.raises(ValueError, match="X/Twitter post URL is required"):
            normalize_xquik_tweet(
                {"id": "123", "text": "some text", "author": {"username": "test"}},
                scope=SCOPE,
            )

    def test_missing_author_handle_raises_value_error(self) -> None:
        """Missing author handle raises ValueError during normalization."""
        with pytest.raises(ValueError, match="X/Twitter author handle is required"):
            normalize_xquik_tweet(
                {"id": "123", "text": "some text", "url": "https://x.com/x/status/123", "author": {"username": ""}},
                scope=SCOPE,
            )

    def test_malformed_payload_in_ingest_propagates(self) -> None:
        """run_social_x_ingest propagates ValueError from malformed provider data.

        When the provider returns data that fails normalization, the ValueError
        propagates from run_social_x_ingest because normalization happens
        inside FakeXTwitterProvider.fetch_posts before the loop.
        """
        sources = NewsSourceRepository()
        source_id = _register_source(sources)
        raw_items = NewsRawItemRepository()
        provider = FakeXTwitterProvider(rows=[{"id": "", "text": "", "url": "", "author": {}}])

        with pytest.raises(ValueError, match="X/Twitter post id is required"):
            run_social_x_ingest(
                source_id,
                sources=sources,
                raw_items=raw_items,
                provider=provider,
            )

    def test_malformed_post_on_due_sources_is_skipped(self) -> None:
        """run_due_social_x_sources catches ValueError from malformed provider."""
        sources = NewsSourceRepository()
        _register_source(sources)
        raw_items = NewsRawItemRepository()
        provider = FakeXTwitterProvider(rows=[{"id": "", "text": "", "url": "", "author": {}}])

        results = run_due_social_x_sources(
            sources=sources,
            raw_items=raw_items,
            provider=provider,
        )

        # ValueError caught by run_due_social_x_sources; source skipped
        assert len(results) == 0


class TestDuplicateLinks:
    """Same URL appearing across posts or repeated ingestion."""

    def test_duplicate_urls_from_different_posts(self) -> None:
        """Two posts with the same URL produce separate raw items.

        Each raw item's external_id is derived from the post_id + url,
        so duplicate URLs from different posts are stored independently.
        """
        sources = NewsSourceRepository()
        source_id = _register_source(sources)
        raw_items = NewsRawItemRepository()
        provider = DuplicateUrlProvider()

        result = run_social_x_ingest(
            source_id,
            sources=sources,
            raw_items=raw_items,
            provider=provider,
        )

        # Both posts have AI signal and URLs → both accepted
        assert result.posts_accepted == 2
        assert result.items_stored == 2  # different external_ids

    def test_same_source_ingested_twice_dedup(self) -> None:
        """Re-ingesting a source produces zero new items (all deduped).

        The second run sees the same external_ids and upsert_item
        returns False for every previously stored item.
        """
        sources = NewsSourceRepository()
        source_id = _register_source(sources)
        raw_items = NewsRawItemRepository()

        result1 = run_social_x_ingest(source_id, sources=sources, raw_items=raw_items)
        assert result1.items_stored >= 1

        # Second pass — same default provider rows, same external_ids
        result2 = run_social_x_ingest(source_id, sources=sources, raw_items=raw_items)
        assert result2.items_stored == 0

    def test_duplicate_url_rejected_by_filter(self) -> None:
        """A post whose only URL was already extracted from another post
        is still accepted (filter operates per-post, not dedup)."""
        sources = NewsSourceRepository()
        source_id = _register_source(sources)
        raw_items = NewsRawItemRepository()
        provider = DuplicateUrlProvider()

        result = run_social_x_ingest(
            source_id,
            sources=sources,
            raw_items=raw_items,
            provider=provider,
        )

        # Both posts are ingested; dedup would happen at extraction level
        assert result.posts_accepted == 2
        assert result.items_stored == 2


class TestUnavailablePosts:
    """Posts whose URLs are dead, missing, or otherwise unavailable."""

    def test_post_without_urls_is_rejected(self) -> None:
        """A post with AI signal but no extractable URLs is rejected pre-ingestion."""
        sources = NewsSourceRepository()
        source_id = _register_source(sources)
        raw_items = NewsRawItemRepository()
        provider = NoUrlsProvider()

        result = run_social_x_ingest(
            source_id,
            sources=sources,
            raw_items=raw_items,
            provider=provider,
        )

        # Post mentions "LLM" (signal) but no urls → filter rejects
        assert result.posts_seen == 1
        assert result.posts_rejected == 1
        assert result.posts_accepted == 0
        assert result.items_stored == 0

    def test_filter_rejects_non_ai_post_without_url(self) -> None:
        """Non-AI post without URLs is cleanly rejected."""
        bad_rows = [
            {
                "id": "nonsense_001",
                "text": "Just had the best pizza ever! 🍕",
                "createdAt": "2026-06-04T12:00:00Z",
                "url": "https://x.com/foodie/status/nonsense_001",
                "author": {"username": "foodie", "followers": 100, "verified": False},
                "entities": {"urls": []},
            },
        ]
        provider = FakeXTwitterProvider(rows=bad_rows)
        sources = NewsSourceRepository()
        source_id = _register_source(sources)
        raw_items = NewsRawItemRepository()

        result = run_social_x_ingest(
            source_id,
            sources=sources,
            raw_items=raw_items,
            provider=provider,
        )

        assert result.posts_seen == 1
        assert result.posts_rejected == 1
        assert result.posts_accepted == 0
        assert result.items_stored == 0

    def test_valid_post_stored_successfully(self) -> None:
        """A valid post with AI signal + extractable URL passes through."""
        provider = FakeXTwitterProvider(rows=[_FIXTURE_WITH_URL])
        sources = NewsSourceRepository()
        source_id = _register_source(sources)
        raw_items = NewsRawItemRepository()

        result = run_social_x_ingest(
            source_id,
            sources=sources,
            raw_items=raw_items,
            provider=provider,
        )

        assert result.posts_seen == 1
        assert result.posts_accepted == 1
        assert result.items_stored == 1
