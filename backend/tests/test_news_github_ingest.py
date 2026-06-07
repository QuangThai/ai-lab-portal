"""Tests for GitHub release ingestion (news_github_ingest)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from backend.app.news_crawl import NewsRawItemRepository
from backend.app.news_github_ingest import (
    GITHUB_FIXTURE_RELEASES,
    GitHubReleaseProvider,
    _parse_repo_path,
    run_due_github_sources,
    run_github_fetch,
)
from backend.app.news_sources import NewsSource, NewsSourceCreate, NewsSourceRepository


def _github_source(
    source_id: str = "newssrc_test_github",
    *,
    enabled: bool = True,
    identifier: str = "openai/openai-cookbook",
    last_crawled_at: datetime | None = None,
) -> NewsSource:
    now = datetime.now(UTC)
    return NewsSource(
        id=source_id,
        name="Test GitHub Repo",
        source_type="github",
        url_or_identifier=identifier,
        description="Test source",
        priority="medium",
        crawl_frequency_minutes=60,
        is_enabled=enabled,
        credibility_base_score=0.8,
        last_crawled_at=last_crawled_at,
        created_at=now,
        updated_at=now,
    )


class TestGitHubReleaseProvider:
    def test_fake_provider_returns_matching_releases(self) -> None:
        provider = GitHubReleaseProvider(fake=True)
        releases = provider.fetch_releases("openai", "openai-agents-python")
        assert len(releases) >= 1
        assert releases[0]["repo"] == "openai/openai-agents-python"
        assert "tag_name" in releases[0]
        assert "html_url" in releases[0]

    def test_fake_provider_returns_fallback_for_unknown_repo(self) -> None:
        provider = GitHubReleaseProvider(fake=True)
        releases = provider.fetch_releases("unknown", "repo")
        assert len(releases) == 1
        assert releases[0]["tag_name"] == "v1.0.0"


class TestParseRepoPath:
    def test_parses_owner_repo(self) -> None:
        assert _parse_repo_path("openai/openai-cookbook") == ("openai", "openai-cookbook")

    def test_parses_full_url(self) -> None:
        assert _parse_repo_path("https://github.com/openai/openai-agents-python") == (
            "openai",
            "openai-agents-python",
        )

    def test_parses_releases_url(self) -> None:
        assert _parse_repo_path("https://github.com/openai/openai-agents-python/releases") == (
            "openai",
            "openai-agents-python",
        )


class TestRunGitHubFetch:
    def test_fetch_accepts_github_source(self) -> None:
        sources = NewsSourceRepository()
        source = sources.create(
            NewsSourceCreate(
                name="Test GitHub",
                source_type="github",
                url_or_identifier="openai/openai-agents-python",
                priority="medium",
                crawl_frequency_minutes=60,
            )
        )
        raw_items = NewsRawItemRepository()

        result = run_github_fetch(source.id, sources=sources, raw_items=raw_items)

        assert result.source_id == source.id
        assert result.releases_seen > 0
        assert result.items_stored > 0

    def test_fetch_nonexistent_source(self) -> None:
        sources = NewsSourceRepository()
        raw_items = NewsRawItemRepository()
        with pytest.raises(ValueError, match="GitHub source not found"):
            run_github_fetch("nonexistent", sources=sources, raw_items=raw_items)

    def test_fetch_wrong_source_type(self) -> None:
        sources = NewsSourceRepository()
        source = sources.create(
            NewsSourceCreate(
                name="Test RSS",
                source_type="rss",
                url_or_identifier="https://example.com/rss",
                priority="medium",
            )
        )
        raw_items = NewsRawItemRepository()
        with pytest.raises(ValueError, match="is not a github source"):
            run_github_fetch(source.id, sources=sources, raw_items=raw_items)

    def test_fetch_disabled_source(self) -> None:
        sources = NewsSourceRepository()
        src = _github_source(enabled=False)
        sources._sources[src.id] = src
        raw_items = NewsRawItemRepository()
        with pytest.raises(ValueError, match="is disabled"):
            run_github_fetch(src.id, sources=sources, raw_items=raw_items)

    def test_fetch_touches_last_crawled(self) -> None:
        sources = NewsSourceRepository()
        src = _github_source()
        sources._sources[src.id] = src
        raw_items = NewsRawItemRepository()

        assert sources.get_by_id(src.id) is not None
        assert sources.get_by_id(src.id).last_crawled_at is None  # type: ignore[union-attr]

        run_github_fetch(src.id, sources=sources, raw_items=raw_items)

        assert sources.get_by_id(src.id).last_crawled_at is not None

    def test_fetch_skips_duplicate_external_ids(self) -> None:
        """Running fetch twice produces no additional stored items."""
        sources = NewsSourceRepository()
        src = _github_source()
        sources._sources[src.id] = src
        raw_items = NewsRawItemRepository()

        first = run_github_fetch(src.id, sources=sources, raw_items=raw_items)
        second = run_github_fetch(src.id, sources=sources, raw_items=raw_items)

        assert first.items_stored > 0
        assert second.items_stored == 0  # all duplicates


class TestRunDueGitHubSources:
    def test_run_due_sources_ingests_due(self) -> None:
        sources = NewsSourceRepository(sources=[])  # empty, no defaults
        src = _github_source()
        sources._sources[src.id] = src
        raw_items = NewsRawItemRepository()

        results = run_due_github_sources(sources=sources, raw_items=raw_items)
        assert len(results) == 1
        assert results[0].items_stored > 0

    def test_run_due_skips_non_github(self) -> None:
        sources = NewsSourceRepository(sources=[])  # empty, no defaults
        sources._sources["rss_src"] = _github_source(
            source_id="rss_src", identifier="https://example.com/rss"
        )
        sources._sources["rss_src"].source_type = "rss"
        github_src = _github_source(source_id="github_src")
        sources._sources[github_src.id] = github_src
        raw_items = NewsRawItemRepository()

        results = run_due_github_sources(sources=sources, raw_items=raw_items)
        assert len(results) == 1

    def test_run_due_skips_not_yet_due(self) -> None:
        sources = NewsSourceRepository(sources=[])  # empty, no defaults
        recent = datetime.now(UTC)
        src = _github_source(last_crawled_at=recent)
        sources._sources[src.id] = src
        raw_items = NewsRawItemRepository()

        results = run_due_github_sources(sources=sources, raw_items=raw_items)
        assert len(results) == 0  # not due yet
