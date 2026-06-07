"""Tests for RSS crawl and raw item storage (US-037)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    sign_admin_identity,
)
from backend.app.main import create_app
from backend.app.news_crawl import (
    NewsRawItemRepository,
    ParsedFeedItem,
    RssFetchError,
    UnsafeUrlError,
    content_hash_for_item,
    parse_rss_or_atom_xml,
    run_crawl_due_rss_sources,
    run_rss_crawl,
    validate_fetch_url,
    _parse_datetime,
    _parse_rss_item,
    _parse_atom_entry,
)
from backend.app.news_sources import NewsSource, NewsSourceCreate, NewsSourceRepository
from backend.app.settings import Settings

TEST_SECRET = "test-admin-boundary-secret-at-least-32-chars"
FIXTURE_RSS = Path(__file__).parent / "fixtures" / "sample.rss.xml"
FIXTURE_ATOM = Path(__file__).parent / "fixtures" / "sample.atom.xml"


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


def _rss_source(repo: NewsSourceRepository) -> NewsSource:
    return repo.create(
        NewsSourceCreate(
            name="Fixture RSS",
            source_type="rss",
            url_or_identifier="https://example.com/feed.xml",
            crawl_frequency_minutes=60,
            is_enabled=True,
        )
    )


# ===========================================================================
# Existing tests (preserved)
# ===========================================================================


def test_validate_fetch_url_blocks_loopback() -> None:
    with pytest.raises(UnsafeUrlError):
        validate_fetch_url("http://127.0.0.1/feed.xml")


def test_parse_rss_fixture() -> None:
    items = parse_rss_or_atom_xml(FIXTURE_RSS.read_bytes())
    assert len(items) == 2
    assert items[0].external_id == "post-first"
    assert items[0].link_url == "https://example.com/posts/first"


def test_run_rss_crawl_stores_items_and_updates_last_crawled() -> None:
    sources = NewsSourceRepository(sources=[])
    raw = NewsRawItemRepository()
    source = _rss_source(sources)

    def fetch(_url: str) -> bytes:
        return FIXTURE_RSS.read_bytes()

    result = run_rss_crawl(source.id, sources=sources, raw_items=raw, fetcher=fetch)
    assert result.items_seen == 2
    assert result.items_stored == 2
    assert result.items_skipped == 0

    stored = raw.list_for_source(source.id)
    assert len(stored) == 2

    updated = sources.get_by_id(source.id)
    assert updated is not None
    assert updated.last_crawled_at is not None

    second = run_rss_crawl(source.id, sources=sources, raw_items=raw, fetcher=fetch)
    assert second.items_seen == 2
    assert second.items_stored == 0
    assert second.items_skipped == 2


def test_run_crawl_due_rss_sources_respects_frequency() -> None:
    now = datetime.now(UTC)
    sources = NewsSourceRepository(sources=[])
    raw = NewsRawItemRepository()
    source = _rss_source(sources)
    sources.touch_last_crawled(source.id, now)

    def fetch(_url: str) -> bytes:
        return FIXTURE_RSS.read_bytes()

    assert run_crawl_due_rss_sources(sources=sources, raw_items=raw, fetcher=fetch) == []

    crawled_at = now - timedelta(minutes=120)
    sources.touch_last_crawled(source.id, crawled_at)
    results = run_crawl_due_rss_sources(sources=sources, raw_items=raw, fetcher=fetch)
    assert len(results) == 1
    assert results[0].items_stored == 2


def test_admin_crawl_endpoint_sync_for_rss(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = NewsSourceRepository(sources=[])
    client = TestClient(create_app(settings=_test_settings(), news_source_repository=repo))
    source = _rss_source(repo)

    monkeypatch.setattr(
        "backend.app.news_crawl.default_fetch_url",
        lambda _url: FIXTURE_RSS.read_bytes(),
    )

    response = client.post(
        f"/admin/news-sources/{source.id}/crawl",
        headers=_admin_headers(),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["items_seen"] == 2
    assert body["items_stored"] == 2


def test_admin_crawl_rejects_non_rss_source() -> None:
    repo = NewsSourceRepository(sources=[])
    client = TestClient(create_app(settings=_test_settings(), news_source_repository=repo))
    website = repo.create(
        NewsSourceCreate(
            name="Website",
            source_type="website",
            url_or_identifier="https://example.com/news",
        )
    )
    response = client.post(
        f"/admin/news-sources/{website.id}/crawl",
        headers=_admin_headers(),
    )
    assert response.status_code == 400
    assert "not supported" in response.json()["detail"]


# ===========================================================================
# Additional: SSRF / URL validation
# ===========================================================================


def test_validate_fetch_url_blocks_private_ip() -> None:
    with pytest.raises(UnsafeUrlError):
        validate_fetch_url("http://10.0.0.1/feed.xml")


def test_validate_fetch_url_blocks_link_local() -> None:
    with pytest.raises(UnsafeUrlError):
        validate_fetch_url("http://169.254.1.1/feed.xml")


def test_validate_fetch_url_blocks_multicast() -> None:
    with pytest.raises(UnsafeUrlError):
        validate_fetch_url("http://224.0.0.1/feed.xml")


def test_validate_fetch_url_rejects_wrong_scheme() -> None:
    with pytest.raises(UnsafeUrlError, match="Only http and https"):
        validate_fetch_url("ftp://example.com/feed.xml")


def test_validate_fetch_url_rejects_no_hostname() -> None:
    with pytest.raises(UnsafeUrlError, match="must include a hostname"):
        validate_fetch_url("http:///feed.xml")


def test_validate_fetch_url_rejects_unresolvable_host() -> None:
    with pytest.raises(UnsafeUrlError, match="Cannot resolve host"):
        validate_fetch_url("http://this-does-not-exist-12345.example/feed.xml")


# ===========================================================================
# Additional: _parse_datetime
# ===========================================================================


class TestParseDatetime:
    """Tests for the _parse_datetime internal helper."""

    def test_returns_none_for_empty(self) -> None:
        assert _parse_datetime(None) is None
        assert _parse_datetime("") is None

    def test_parses_rfc2822_without_timezone(self) -> None:
        result = _parse_datetime("Mon, 01 Jun 2026 12:00:00 GMT")
        assert result is not None
        assert result.tzinfo is not None

    def test_parses_rfc3339_with_z(self) -> None:
        result = _parse_datetime("2026-06-01T12:00:00Z")
        assert result is not None
        assert result.tzinfo is not None

    def test_parses_rfc3339_with_offset(self) -> None:
        result = _parse_datetime("2026-06-01T12:00:00+00:00")
        assert result is not None

    def test_returns_none_on_garbage(self) -> None:
        assert _parse_datetime("not-a-date") is None

    def test_returns_none_on_malformed(self) -> None:
        assert _parse_datetime("2026-99-99T99:99:99Z") is None


# ===========================================================================
# Additional: content_hash_for_item
# ===========================================================================


class TestContentHashForItem:
    """Tests for content_hash_for_item."""

    def test_deterministic_hash(self) -> None:
        item = ParsedFeedItem(
            external_id="e1",
            title="Test",
            link_url="https://example.com",
            published_at=None,
            raw_payload={"format": "rss2", "title": "Test"},
        )
        h1 = content_hash_for_item(item)
        h2 = content_hash_for_item(item)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex

    def test_different_items_different_hash(self) -> None:
        item_a = ParsedFeedItem(
            external_id="a", title="A", link_url="https://a.com",
            published_at=None, raw_payload={"format": "rss2"},
        )
        item_b = ParsedFeedItem(
            external_id="b", title="B", link_url="https://b.com",
            published_at=None, raw_payload={"format": "rss2"},
        )
        assert content_hash_for_item(item_a) != content_hash_for_item(item_b)


# ===========================================================================
# Additional: Atom feed parsing
# ===========================================================================


class TestParseAtom:
    """Tests for Atom feed parsing."""

    def test_parse_atom_fixture(self) -> None:
        items = parse_rss_or_atom_xml(FIXTURE_ATOM.read_bytes())
        assert len(items) == 2
        # First entry: published date with id
        assert items[0].external_id == "atom-entry-1"
        assert items[0].link_url == "https://example.com/atom/first"
        assert items[0].title == "Atom First Post"
        assert items[0].published_at is not None

    def test_atom_entry_missing_id_and_link_returns_none(self) -> None:
        body = (
            b'<?xml version="1.0"?><feed>'
            b"<entry><title>No ID</title></entry></feed>"
        )
        items = parse_rss_or_atom_xml(body)
        assert len(items) == 0  # entry without id+link is skipped

    def test_atom_entry_uses_updated_when_no_published(self) -> None:
        body = (
            b'<?xml version="1.0"?><feed>'
            b"<entry><id>e1</id><title>T</title>"
            b'<link href="https://example.com/e1"/>'
            b"<updated>2026-06-02T12:00:00Z</updated>"
            b"</entry></feed>"
        )
        items = parse_rss_or_atom_xml(body)
        assert len(items) == 1
        assert items[0].published_at is not None


# ===========================================================================
# Additional: RSS parsing edge cases
# ===========================================================================


class TestParseRssEdgeCases:
    """Edge cases for RSS parsing."""

    def test_empty_channel_returns_empty(self) -> None:
        body = b'<?xml version="1.0"?><rss version="2.0"><channel></channel></rss>'
        items = parse_rss_or_atom_xml(body)
        assert items == []

    def test_missing_guid_and_link_returns_none(self) -> None:
        body = (
            b'<?xml version="1.0"?><rss version="2.0"><channel>'
            b"<item><title>No identifiers</title></item>"
            b"</channel></rss>"
        )
        items = parse_rss_or_atom_xml(body)
        assert len(items) == 0

    def test_item_without_title_gets_untitled(self) -> None:
        body = (
            b'<?xml version="1.0"?><rss version="2.0"><channel>'
            b"<item><link>https://example.com/x</link></item>"
            b"</channel></rss>"
        )
        items = parse_rss_or_atom_xml(body)
        assert len(items) == 1
        assert items[0].title == "Untitled"

    def test_unsupported_root_element_raises(self) -> None:
        body = b'<?xml version="1.0"?><html><body>Not a feed</body></html>'
        with pytest.raises(RssFetchError, match="Unsupported feed root"):
            parse_rss_or_atom_xml(body)

    def test_invalid_xml_raises(self) -> None:
        with pytest.raises(RssFetchError, match="Invalid RSS/Atom"):
            parse_rss_or_atom_xml(b"not xml")

    def test_uses_guid_as_link_when_no_link(self) -> None:
        body = (
            b'<?xml version="1.0"?><rss version="2.0"><channel>'
            b"<item><guid>just-guid</guid><title>GUID only</title></item>"
            b"</channel></rss>"
        )
        items = parse_rss_or_atom_xml(body)
        assert len(items) == 1
        assert items[0].external_id == "just-guid"
        assert items[0].link_url == "just-guid"


# ===========================================================================
# Additional: NewsRawItemRepository
# ===========================================================================


class TestNewsRawItemRepository:
    """Tests for the in-memory NewsRawItemRepository."""

    def test_get_by_id_returns_none_for_missing(self) -> None:
        repo = NewsRawItemRepository()
        assert repo.get_by_id("nonexistent") is None

    def test_get_by_id_returns_item(self) -> None:
        repo = NewsRawItemRepository()
        source_id = "src1"
        item = ParsedFeedItem(
            external_id="e1", title="T", link_url="https://x.com",
            published_at=None, raw_payload={},
        )
        repo.upsert_item(
            source_id=source_id, item=item,
            content_hash="abc", fetched_at=datetime.now(UTC),
        )
        stored = repo.list_for_source(source_id)
        assert len(stored) == 1
        fetched = repo.get_by_id(stored[0].id)
        assert fetched is not None
        assert fetched.title == "T"

    def test_list_without_extraction_filters_extracted(self) -> None:
        repo = NewsRawItemRepository()
        source_id = "src1"
        item = ParsedFeedItem(
            external_id="e1", title="T", link_url="https://x.com",
            published_at=None, raw_payload={},
        )
        repo.upsert_item(
            source_id=source_id, item=item,
            content_hash="abc", fetched_at=datetime.now(UTC),
        )

        # Mock extracted repository
        class MockExtracted:
            def get_by_raw_item_id(self, rid: str):
                if rid == repo.list_for_source(source_id)[0].id:
                    return object()  # truthy = already extracted
                return None

        pending = repo.list_without_extraction(MockExtracted(), source_id=source_id)
        assert pending == []

    def test_list_without_extraction_includes_unextracted(self) -> None:
        repo = NewsRawItemRepository()
        source_id = "src1"
        item = ParsedFeedItem(
            external_id="e1", title="T", link_url="https://x.com",
            published_at=None, raw_payload={},
        )
        repo.upsert_item(
            source_id=source_id, item=item,
            content_hash="abc", fetched_at=datetime.now(UTC),
        )

        class MockExtracted:
            def get_by_raw_item_id(self, rid: str):
                return None

        pending = repo.list_without_extraction(MockExtracted(), source_id=source_id)
        assert len(pending) == 1

    def test_list_for_source_empty(self) -> None:
        repo = NewsRawItemRepository()
        assert repo.list_for_source("nonexistent") == []

    def test_list_without_extraction_no_source_filter(self) -> None:
        repo = NewsRawItemRepository()
        for i in range(3):
            item = ParsedFeedItem(
                external_id=f"e{i}", title=f"T{i}", link_url=f"https://x{i}.com",
                published_at=None, raw_payload={},
            )
            repo.upsert_item(
                source_id="src1", item=item,
                content_hash="abc", fetched_at=datetime.now(UTC),
            )

        class MockExtracted:
            def get_by_raw_item_id(self, rid: str):
                return None

        # Without source_id, returns all
        pending = repo.list_without_extraction(MockExtracted())
        assert len(pending) == 3


# ===========================================================================
# Additional: run_rss_crawl edge cases
# ===========================================================================


class TestRunRssCrawlEdgeCases:
    """Edge cases for run_rss_crawl."""

    def test_raises_for_missing_source(self) -> None:
        sources = NewsSourceRepository(sources=[])
        raw = NewsRawItemRepository()
        with pytest.raises(ValueError, match="News source not found"):
            run_rss_crawl("nonexistent", sources=sources, raw_items=raw)

    def test_raises_for_non_rss_source(self) -> None:
        sources = NewsSourceRepository(sources=[])
        raw = NewsRawItemRepository()
        source = sources.create(
            NewsSourceCreate(
                name="Web", source_type="website",
                url_or_identifier="https://example.com",
            )
        )
        with pytest.raises(ValueError, match="is not an RSS source"):
            run_rss_crawl(source.id, sources=sources, raw_items=raw)

    def test_raises_for_disabled_source(self) -> None:
        sources = NewsSourceRepository(sources=[])
        raw = NewsRawItemRepository()
        source = sources.create(
            NewsSourceCreate(
                name="Disabled", source_type="rss",
                url_or_identifier="https://example.com/feed",
                is_enabled=False,
            )
        )
        with pytest.raises(ValueError, match="is disabled"):
            run_rss_crawl(source.id, sources=sources, raw_items=raw)

    def test_fetch_error_raises_rss_fetch_error(self) -> None:
        sources = NewsSourceRepository(sources=[])
        raw = NewsRawItemRepository()
        source = _rss_source(sources)

        def broken_fetch(_url: str) -> bytes:
            raise UnsafeUrlError("Blocked by SSRF")

        with pytest.raises(RssFetchError, match="Blocked by SSRF"):
            run_rss_crawl(source.id, sources=sources, raw_items=raw, fetcher=broken_fetch)

    def test_parse_error_during_fetch(self) -> None:
        sources = NewsSourceRepository(sources=[])
        raw = NewsRawItemRepository()
        source = _rss_source(sources)

        def bad_xml_fetch(_url: str) -> bytes:
            return b"not valid xml"

        with pytest.raises(RssFetchError, match="Invalid RSS/Atom"):
            run_rss_crawl(source.id, sources=sources, raw_items=raw, fetcher=bad_xml_fetch)


# ===========================================================================
# Additional: run_crawl_due_rss_sources edge cases
# ===========================================================================


class TestRunCrawlDueRssSources:
    """Tests for run_crawl_due_rss_sources."""

    def test_empty_when_no_sources(self) -> None:
        sources = NewsSourceRepository(sources=[])
        raw = NewsRawItemRepository()
        results = run_crawl_due_rss_sources(sources=sources, raw_items=raw)
        assert results == []

    def test_handles_rss_fetch_error_gracefully(self) -> None:
        sources = NewsSourceRepository(sources=[])
        raw = NewsRawItemRepository()
        _rss_source(sources)  # due immediately (never crawled)

        def failing_fetch(_url: str) -> bytes:
            raise RssFetchError("Network error")

        results = run_crawl_due_rss_sources(
            sources=sources, raw_items=raw, fetcher=failing_fetch,
        )
        assert results == []  # error is caught and skipped

    def test_crawls_only_due_sources(self) -> None:
        now = datetime.now(UTC)
        sources = NewsSourceRepository(sources=[])
        raw = NewsRawItemRepository()

        # Source A: never crawled -> due
        src_a = _rss_source(sources)
        # Source B: just crawled -> not due
        src_b = sources.create(
            NewsSourceCreate(
                name="Not Due", source_type="rss",
                url_or_identifier="https://example.com/feed2",
                crawl_frequency_minutes=60,
                is_enabled=True,
            )
        )
        sources.touch_last_crawled(src_b.id, now)

        def fetch(_url: str) -> bytes:
            return FIXTURE_RSS.read_bytes()

        results = run_crawl_due_rss_sources(sources=sources, raw_items=raw, fetcher=fetch)
        assert len(results) == 1
        assert results[0].source_id == src_a.id


# ===========================================================================
# Additional: _parse_rss_item and _parse_atom_entry directly
# ===========================================================================


class TestParseRssItem:
    """Direct tests for _parse_rss_item."""

    def test_returns_none_when_no_guid_and_no_link(self) -> None:
        from xml.etree import ElementTree
        el = ElementTree.fromstring("<item><title>X</title></item>")
        result = _parse_rss_item(el)
        assert result is None

    def test_uses_guid_as_external_id(self) -> None:
        from xml.etree import ElementTree
        el = ElementTree.fromstring(
            '<item><guid>my-guid</guid><title>X</title></item>'
        )
        result = _parse_rss_item(el)
        assert result is not None
        assert result.external_id == "my-guid"


class TestParseAtomEntry:
    """Direct tests for _parse_atom_entry."""

    def test_returns_none_when_no_id_and_no_link(self) -> None:
        from xml.etree import ElementTree
        el = ElementTree.fromstring(
            '<entry><title>X</title></entry>'
        )
        result = _parse_atom_entry(el)
        assert result is None

    def test_extracts_title_from_entry(self) -> None:
        from xml.etree import ElementTree
        el = ElementTree.fromstring(
            '<entry>'
            '<id>e1</id><title>Hello</title>'
            '<link href="https://x.com"/></entry>'
        )
        result = _parse_atom_entry(el)
        assert result is not None
        assert result.title == "Hello"

    def test_uses_id_as_fallback_for_link(self) -> None:
        from xml.etree import ElementTree
        el = ElementTree.fromstring(
            '<entry>'
            '<id>just-id</id><title>T</title></entry>'
        )
        result = _parse_atom_entry(el)
        assert result is not None
        assert result.link_url == "just-id"
        assert result.external_id == "just-id"
