"""X/Twitter social ingestion spike with fake provider (US-055).

This module connects the FakeXTwitterProvider and social link filter to the
existing AI News pipeline. It produces raw items from accepted social posts
and triggers extraction — all without any real provider API calls.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from backend.app.news_crawl import ParsedFeedItem
from backend.app.social_x import (
    FAKE_XQUIK_ROWS,
    FakeXTwitterProvider,
    SocialPostSourceScope,
    filter_social_link_candidate,
)

if TYPE_CHECKING:
    from backend.app.news_crawl import NewsRawItemRepository
    from backend.app.news_sources import NewsSource, NewsSourceRepository


class SocialIngestionResult:
    """Outcome of one social source ingestion run."""

    def __init__(
        self,
        *,
        source_id: str,
        posts_seen: int = 0,
        posts_accepted: int = 0,
        posts_rejected: int = 0,
        items_stored: int = 0,
    ) -> None:
        self.source_id = source_id
        self.posts_seen = posts_seen
        self.posts_accepted = posts_accepted
        self.posts_rejected = posts_rejected
        self.items_stored = items_stored

    def model_dump(self) -> dict:
        return {
            "source_id": self.source_id,
            "posts_seen": self.posts_seen,
            "posts_accepted": self.posts_accepted,
            "posts_rejected": self.posts_rejected,
            "items_stored": self.items_stored,
        }


def _social_post_to_raw_item(
    post,
    *,
    source_id: str,
    fetched_at: datetime,
) -> ParsedFeedItem:
    """Convert an accepted social post to a ParsedFeedItem for the raw items table."""
    link_url = str(post.post_url)
    return ParsedFeedItem(
        external_id=f"social_{post.provider}_{post.post_id}",
        title=post.post_text[:80],
        link_url=link_url,
        published_at=post.created_at,
        raw_payload={
            "social_provider": post.provider,
            "social_provider_actor": post.provider_actor,
            "social_post_id": post.post_id,
            "social_author_handle": post.author_handle,
            "social_author_display_name": post.author_display_name or "",
            "social_filter_decision": {},
        },
    )


def _build_source_scope(source: NewsSource) -> SocialPostSourceScope:
    """Build a SocialPostSourceScope from a NewsSource config.

    The url_or_identifier stores the social handle or search keyword.
    """
    return SocialPostSourceScope(
        provider="fake",
        provider_actor="fake_xquik_v1",
        source_kind="handle",
        source_value=source.url_or_identifier,
        matched_query=None,
        crawl_run_id=f"crawl_{uuid4().hex[:12]}",
    )


def run_social_x_ingest(
    source_id: str,
    *,
    sources: NewsSourceRepository,
    raw_items: NewsRawItemRepository,
    provider: FakeXTwitterProvider | None = None,
) -> SocialIngestionResult:
    """Ingest X/Twitter posts for one source using the fake provider.

    Args:
        source_id: The news source ID to ingest.
        sources: NewsSourceRepository for source config lookup.
        raw_items: NewsRawItemRepository for storing accepted raw items.
        provider: Optional FakeXTwitterProvider (uses default FAKE_XQUIK_ROWS).

    Returns:
        SocialIngestionResult with counts of seen/accepted/stored items.
    """
    source = sources.get_by_id(source_id)
    if source is None:
        raise ValueError(f"Social source not found: {source_id}")
    if source.source_type != "social_x":
        raise ValueError(f"Source {source_id} is not a social_x source (type={source.source_type})")
    if not source.is_enabled:
        raise ValueError(f"Source {source_id} is disabled")

    scope = _build_source_scope(source)
    fetcher = provider or FakeXTwitterProvider()
    posts = fetcher.fetch_posts(scope)
    fetched_at = datetime.now(UTC)

    result = SocialIngestionResult(source_id=source_id, posts_seen=len(posts))

    for post in posts:
        decision = filter_social_link_candidate(post)

        if not decision.should_ingest:
            result.posts_rejected += 1
            continue

        result.posts_accepted += 1

        # For accepted posts with URLs, create raw items for each extractable URL
        for url in decision.urls_to_extract:
            feed_item = ParsedFeedItem(
                external_id=f"social_{post.provider}_{post.post_id}_{url}",
                title=post.post_text[:80],
                link_url=str(url),
                published_at=post.created_at,
                raw_payload={
                    "social_provider": post.provider,
                    "social_provider_actor": post.provider_actor,
                    "social_post_id": post.post_id,
                    "social_post_text": post.post_text,
                    "social_author_handle": post.author_handle,
                    "social_filter_decision": decision.model_dump(),
                },
            )

            item_id = f"newsraw_{uuid4().hex}"
            content_hash = f"sha256:{item_id}"  # unique per raw item
            if raw_items.upsert_item(
                source_id=source_id,
                item=feed_item,
                content_hash=content_hash,
                fetched_at=fetched_at,
            ):
                result.items_stored += 1

    sources.touch_last_crawled(source_id, fetched_at)
    return result


def run_due_social_x_sources(
    *,
    sources: NewsSourceRepository,
    raw_items: NewsRawItemRepository,
    provider: FakeXTwitterProvider | None = None,
) -> list[SocialIngestionResult]:
    """Ingest all due social_x sources."""
    from datetime import timedelta

    now = datetime.now(UTC)
    results: list[SocialIngestionResult] = []

    for source in sources.list_all():
        src = sources.get_by_id(source.id)
        if not src or not src.is_enabled or src.source_type != "social_x":
            continue
        if src.last_crawled_at is not None:
            if src.last_crawled_at + timedelta(minutes=src.crawl_frequency_minutes) > now:
                continue
        try:
            results.append(
                run_social_x_ingest(
                    src.id,
                    sources=sources,
                    raw_items=raw_items,
                    provider=provider,
                )
            )
        except ValueError:
            continue

    return results
