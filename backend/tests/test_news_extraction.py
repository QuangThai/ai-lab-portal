"""Tests for article extraction from news raw items (US-038)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    sign_admin_identity,
)
from backend.app.main import create_app
from backend.app.news_crawl import NewsRawItemRepository, ParsedFeedItem, run_rss_crawl
from backend.app.news_extraction import (
    ExtractedArticleRepository,
    ExtractionError,
    ExtractionOutput,
    FakeArticleExtractor,
    FirecrawlArticleExtractor,
    ArticleExtractor,
    content_hash,
    extractor_for_settings,
    run_extract_pending_raw_items,
    run_extract_raw_item,
    _best_article_url,
)
from backend.app.news_sources import NewsSourceRepository
from backend.app.settings import Settings
from backend.tests.test_news_crawl import FIXTURE_RSS, _rss_source

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


def _seed_raw_item() -> tuple[NewsSourceRepository, NewsRawItemRepository, str, str]:
    sources = NewsSourceRepository(sources=[])
    raw = NewsRawItemRepository()
    source = _rss_source(sources)
    run_rss_crawl(
        source.id,
        sources=sources,
        raw_items=raw,
        fetcher=lambda _url: FIXTURE_RSS.read_bytes(),
    )
    raw_item = raw.list_for_source(source.id)[0]
    return sources, raw, source.id, raw_item.id


# ===========================================================================
# Existing tests (preserved)
# ===========================================================================


def test_run_extract_raw_item_success() -> None:
    _sources, raw, _source_id, raw_item_id = _seed_raw_item()
    extracted = ExtractedArticleRepository()
    result = run_extract_raw_item(
        raw_item_id,
        raw_items=raw,
        extracted=extracted,
        extractor=FakeArticleExtractor(),
    )
    assert result.status == "success"
    row = extracted.get_by_raw_item_id(raw_item_id)
    assert row is not None
    assert row.extraction_status == "success"
    assert "Stub article body" in row.content_markdown


def test_run_extract_pending_only_unextracted() -> None:
    sources, raw, source_id, raw_item_id = _seed_raw_item()
    extracted = ExtractedArticleRepository()
    extractor = FakeArticleExtractor()
    run_extract_raw_item(raw_item_id, raw_items=raw, extracted=extracted, extractor=extractor)
    results = run_extract_pending_raw_items(
        raw_items=raw,
        extracted=extracted,
        extractor=extractor,
        source_id=source_id,
    )
    assert len(results) == 1
    assert results[0].status == "success"

    for item in raw.list_for_source(source_id):
        run_extract_raw_item(item.id, raw_items=raw, extracted=extracted, extractor=extractor)
    assert (
        run_extract_pending_raw_items(
            raw_items=raw,
            extracted=extracted,
            extractor=extractor,
            source_id=source_id,
        )
        == []
    )


def test_admin_extract_and_list_endpoints() -> None:
    sources, raw, source_id, raw_item_id = _seed_raw_item()
    extracted = ExtractedArticleRepository()
    client = TestClient(
        create_app(
            settings=_test_settings(),
            news_source_repository=sources,
            news_raw_item_repository=raw,
            extracted_article_repository=extracted,
        )
    )

    listed = client.get(
        f"/admin/news-sources/{source_id}/raw-items",
        headers=_admin_headers(),
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 2

    extract_resp = client.post(
        f"/admin/news-sources/raw-items/{raw_item_id}/extract",
        headers=_admin_headers(),
    )
    assert extract_resp.status_code == 200
    assert extract_resp.json()["status"] == "success"

    got = client.get(
        f"/admin/news-sources/raw-items/{raw_item_id}/extraction",
        headers=_admin_headers(),
    )
    assert got.status_code == 200
    assert got.json()["extraction_status"] == "success"


# ===========================================================================
# Additional: content_hash and _best_article_url helpers
# ===========================================================================


class TestContentHash:
    """Tests for the content_hash helper."""

    def test_returns_sha256_hex(self) -> None:
        h = content_hash("# Hello", "Hello")
        assert len(h) == 64

    def test_deterministic(self) -> None:
        h1 = content_hash("abc", "def")
        h2 = content_hash("abc", "def")
        assert h1 == h2

    def test_different_input_different_hash(self) -> None:
        h1 = content_hash("abc", "def")
        h2 = content_hash("abc", "xyz")
        assert h1 != h2


class TestBestArticleUrl:
    """Tests for the _best_article_url helper."""

    def test_canonical_wins(self) -> None:
        url = _best_article_url(
            source_url="https://src.com/a",
            final_url="https://final.com/a",
            canonical_url="https://canonical.com/a",
        )
        assert url == "https://canonical.com/a"

    def test_fallback_to_final(self) -> None:
        url = _best_article_url(
            source_url="https://src.com/a",
            final_url="https://final.com/a",
            canonical_url=None,
        )
        assert url == "https://final.com/a"

    def test_fallback_to_source(self) -> None:
        url = _best_article_url(
            source_url="https://src.com/a",
            final_url=None,
            canonical_url=None,
        )
        assert url == "https://src.com/a"


# ===========================================================================
# Additional: extractor_for_settings
# ===========================================================================


class TestExtractorForSettings:
    """Tests for extractor_for_settings."""

    def test_test_env_returns_fake(self) -> None:
        settings = Settings(environment="test", admin_boundary_secret="a-we-need-at-least-32-chars-here!!")
        extractor = extractor_for_settings(settings)
        assert isinstance(extractor, FakeArticleExtractor)

    def test_dev_with_no_firecrawl_key_returns_fake(self) -> None:
        settings = Settings(
            environment="development",
            admin_boundary_secret="a-we-need-at-least-32-chars-here!!",
            firecrawl_api_key="",
        )
        extractor = extractor_for_settings(settings)
        assert isinstance(extractor, FakeArticleExtractor)

    def test_dev_with_firecrawl_key_returns_firecrawl(self) -> None:
        settings = Settings(
            environment="development",
            admin_boundary_secret="a-we-need-at-least-32-chars-here!!",
            firecrawl_api_key="sk-test-key",
        )
        extractor = extractor_for_settings(settings)
        assert isinstance(extractor, FirecrawlArticleExtractor)


# ===========================================================================
# Additional: FakeArticleExtractor
# ===========================================================================


class TestFakeArticleExtractor:
    """Tests for the FakeArticleExtractor."""

    def test_extract_produces_markdown_and_text(self) -> None:
        raw_item_summary = MagicMock()
        raw_item_summary.title = "Test Article"
        raw_item_summary.link_url = "https://example.com/article"
        raw_item_summary.published_at = datetime.now(UTC)

        extractor = FakeArticleExtractor()
        output = extractor.extract(raw_item_summary)
        assert output.title == "Test Article"
        assert "Stub article body" in output.content_markdown
        assert "Test Article" in output.content_text
        assert output.provider == "fake"
        assert output.provider_latency_ms >= 0
        assert output.provider_payload == {"mode": "fake"}

    def test_extract_includes_link_in_markdown(self) -> None:
        raw_item_summary = MagicMock()
        raw_item_summary.title = "Article"
        raw_item_summary.link_url = "https://example.com/a"
        raw_item_summary.published_at = None

        extractor = FakeArticleExtractor()
        output = extractor.extract(raw_item_summary)
        assert "https://example.com/a" in output.content_markdown


# ===========================================================================
# Additional: ExtractedArticleRepository
# ===========================================================================


class TestExtractedArticleRepository:
    """Tests for the in-memory ExtractedArticleRepository."""

    def test_get_by_id_returns_none_for_missing(self) -> None:
        repo = ExtractedArticleRepository()
        assert repo.get_by_id("nonexistent") is None

    def test_save_success_creates_record(self) -> None:
        repo = ExtractedArticleRepository()
        raw_item = MagicMock(spec=NewsRawItemRepository)
        raw_item.id = "raw_1"
        raw_item.link_url = "https://example.com/article"
        raw_item.title = "Test"
        raw_item.published_at = datetime.now(UTC)

        output = ExtractionOutput(
            final_url="https://example.com/article",
            canonical_url="https://example.com/article",
            title="Test Article",
            author="Author",
            site_name="Example",
            published_at=datetime.now(UTC),
            content_markdown="# Markdown",
            content_text="Markdown",
            provider="fake",
            provider_latency_ms=10,
            provider_payload=None,
        )
        row = repo.save_success(raw_item, output)
        assert row.extraction_status == "success"
        assert row.title == "Test Article"
        assert row.author == "Author"
        assert row.provider == "fake"

    def test_save_failure_creates_record(self) -> None:
        repo = ExtractedArticleRepository()
        raw_item = MagicMock(spec=NewsRawItemRepository)
        raw_item.id = "raw_2"
        raw_item.link_url = "https://example.com/fail"
        raw_item.title = "Failed"
        raw_item.published_at = None

        row = repo.save_failure(raw_item, provider="fake", error="Something broke")
        assert row.extraction_status == "failed"
        assert row.extraction_error == "Something broke"
        assert row.content_markdown == ""
        assert row.content_text == ""

    def test_get_by_raw_item_id(self) -> None:
        repo = ExtractedArticleRepository()
        raw_item = MagicMock(spec=NewsRawItemRepository)
        raw_item.id = "raw_3"
        raw_item.link_url = "https://example.com/3"
        raw_item.title = "Three"
        raw_item.published_at = None

        output = ExtractionOutput(
            final_url="https://example.com/3",
            canonical_url=None,
            title="Three",
            author=None,
            site_name=None,
            published_at=None,
            content_markdown="# T",
            content_text="T",
            provider="fake",
            provider_latency_ms=0,
            provider_payload=None,
        )
        saved = repo.save_success(raw_item, output)
        assert repo.get_by_raw_item_id("raw_3") is saved

    def test_get_by_raw_item_id_returns_none(self) -> None:
        repo = ExtractedArticleRepository()
        assert repo.get_by_raw_item_id("nonexistent") is None

    def test_find_earliest_by_canonical_url(self) -> None:
        repo = ExtractedArticleRepository()
        raw_item = MagicMock(spec=NewsRawItemRepository)
        raw_item.id = "raw_canon"
        raw_item.link_url = "https://example.com/canon"
        raw_item.title = "Canon"
        raw_item.published_at = None

        output = ExtractionOutput(
            final_url="https://example.com/canon",
            canonical_url="https://canonical.com/a",
            title="Canon",
            author=None,
            site_name=None,
            published_at=None,
            content_markdown="# C",
            content_text="C",
            provider="fake",
            provider_latency_ms=0,
            provider_payload=None,
        )
        saved = repo.save_success(raw_item, output)
        found = repo.find_earliest_by_canonical_url(
            "https://canonical.com/a",
            exclude_id=saved.id,
        )
        assert found is None  # no other match

    def test_find_earliest_by_canonical_url_matches_other(self) -> None:
        repo = ExtractedArticleRepository()
        raw_item = MagicMock(spec=NewsRawItemRepository)
        raw_item.id = "raw_a"
        raw_item.link_url = "https://example.com/a"
        raw_item.title = "A"
        raw_item.published_at = None

        output_a = ExtractionOutput(
            final_url="https://example.com/a",
            canonical_url="https://canon.com/x",
            title="A",
            author=None, site_name=None, published_at=None,
            content_markdown="# A", content_text="A",
            provider="fake", provider_latency_ms=0, provider_payload=None,
        )
        saved_a = repo.save_success(raw_item, output_a)

        raw_item_b = MagicMock(spec=NewsRawItemRepository)
        raw_item_b.id = "raw_b"
        raw_item_b.link_url = "https://example.com/b"
        raw_item_b.title = "B"
        raw_item_b.published_at = None

        output_b = ExtractionOutput(
            final_url="https://example.com/b",
            canonical_url="https://canon.com/x",
            title="B",
            author=None, site_name=None, published_at=None,
            content_markdown="# B", content_text="B",
            provider="fake", provider_latency_ms=0, provider_payload=None,
        )
        saved_b = repo.save_success(raw_item_b, output_b)

        found = repo.find_earliest_by_canonical_url(
            "https://canon.com/x",
            exclude_id=saved_b.id,
        )
        assert found == saved_a.id  # earliest is A

    def test_find_earliest_by_content_hash(self) -> None:
        repo = ExtractedArticleRepository()
        raw_item = MagicMock(spec=NewsRawItemRepository)
        raw_item.id = "raw_hash"
        raw_item.link_url = "https://example.com/h"
        raw_item.title = "Hash"
        raw_item.published_at = None

        output = ExtractionOutput(
            final_url="https://example.com/h",
            canonical_url=None,
            title="Hash",
            author=None, site_name=None, published_at=None,
            content_markdown="# H", content_text="H",
            provider="fake", provider_latency_ms=0, provider_payload=None,
        )
        saved = repo.save_success(raw_item, output)
        # find with matching hash
        found = repo.find_earliest_by_content_hash(
            saved.content_hash,
            exclude_id=saved.id,
        )
        assert found is None  # no other match

    def test_find_earliest_by_content_hash_no_match(self) -> None:
        repo = ExtractedArticleRepository()
        result = repo.find_earliest_by_content_hash(
            "nonexistent_hash",
            exclude_id="some_id",
        )
        assert result is None

    def test_update_dedup_fields(self) -> None:
        repo = ExtractedArticleRepository()
        raw_item = MagicMock(spec=NewsRawItemRepository)
        raw_item.id = "raw_dedup"
        raw_item.link_url = "https://example.com/d"
        raw_item.title = "Dedup"
        raw_item.published_at = None

        output = ExtractionOutput(
            final_url="https://example.com/d",
            canonical_url="https://canon.com/d",
            title="Dedup",
            author=None, site_name=None, published_at=None,
            content_markdown="# D", content_text="D",
            provider="fake", provider_latency_ms=0, provider_payload=None,
        )
        saved = repo.save_success(raw_item, output)

        updated = repo.update_dedup_fields(
            saved.id,
            canonical_url_normalized="https://canon.com/d",
            duplicate_status="url_duplicate",
            duplicate_of_id="other_id",
        )
        assert updated is not None
        assert updated.duplicate_status == "url_duplicate"
        assert updated.duplicate_of_id == "other_id"
        assert updated.canonical_url_normalized == "https://canon.com/d"

    def test_update_dedup_fields_returns_none_for_missing(self) -> None:
        repo = ExtractedArticleRepository()
        result = repo.update_dedup_fields(
            "nonexistent",
            canonical_url_normalized="",
            duplicate_status="unique",
            duplicate_of_id=None,
        )
        assert result is None

    def test_save_failure_truncates_long_error(self) -> None:
        repo = ExtractedArticleRepository()
        raw_item = MagicMock(spec=NewsRawItemRepository)
        raw_item.id = "raw_err"
        raw_item.link_url = "https://example.com/e"
        raw_item.title = "Error"
        raw_item.published_at = None

        long_error = "x" * 5000
        row = repo.save_failure(raw_item, provider="fake", error=long_error)
        assert len(row.extraction_error) <= 2000
        assert row.extraction_error == long_error[:2000]


# ===========================================================================
# Additional: run_extract_raw_item failure paths
# ===========================================================================


class TestRunExtractRawItemFailures:
    """Failure paths for run_extract_raw_item."""

    def test_raises_for_missing_raw_item(self) -> None:
        raw = NewsRawItemRepository()
        extracted = ExtractedArticleRepository()
        with pytest.raises(ValueError, match="Raw item not found"):
            run_extract_raw_item(
                "nonexistent",
                raw_items=raw,
                extracted=extracted,
                extractor=FakeArticleExtractor(),
            )

    def test_extraction_error_saves_failure(self) -> None:
        class BrokenExtractor(ArticleExtractor):
            def extract(self, raw_item):
                raise ExtractionError("Provider down")

        sources, raw, _source_id, raw_item_id = _seed_raw_item()
        extracted = ExtractedArticleRepository()
        result = run_extract_raw_item(
            raw_item_id,
            raw_items=raw,
            extracted=extracted,
            extractor=BrokenExtractor(),
        )
        assert result.status == "failed"
        assert "Provider down" in (result.error or "")
        row = extracted.get_by_raw_item_id(raw_item_id)
        assert row is not None
        assert row.extraction_status == "failed"
        assert row.extraction_error == "Provider down"

    def test_value_error_during_extraction_saves_failure(self) -> None:
        class BrokenExtractor(ArticleExtractor):
            def extract(self, raw_item):
                raise ValueError("Invalid data")

        sources, raw, _source_id, raw_item_id = _seed_raw_item()
        extracted = ExtractedArticleRepository()
        result = run_extract_raw_item(
            raw_item_id,
            raw_items=raw,
            extracted=extracted,
            extractor=BrokenExtractor(),
        )
        assert result.status == "failed"
        assert "Invalid data" in (result.error or "")
        row = extracted.get_by_raw_item_id(raw_item_id)
        assert row is not None
        assert row.extraction_status == "failed"


# ===========================================================================
# Additional: run_extract_pending_raw_items edge cases
# ===========================================================================


class TestRunExtractPendingRawItems:
    """Edge cases for run_extract_pending_raw_items."""

    def test_empty_when_no_items(self) -> None:
        raw = NewsRawItemRepository()
        extracted = ExtractedArticleRepository()
        results = run_extract_pending_raw_items(
            raw_items=raw,
            extracted=extracted,
            extractor=FakeArticleExtractor(),
        )
        assert results == []

    def test_handles_multiple_items(self) -> None:
        sources, raw, source_id, raw_item_id = _seed_raw_item()
        extracted = ExtractedArticleRepository()
        results = run_extract_pending_raw_items(
            raw_items=raw,
            extracted=extracted,
            extractor=FakeArticleExtractor(),
            source_id=source_id,
        )
        assert len(results) == 2  # both raw items are pending
        assert all(r.status == "success" for r in results)


# ===========================================================================
# Additional: Admin API error paths
# ===========================================================================


class TestAdminExtractionAPIErrors:
    """Error responses for the extraction admin endpoints."""

    def test_get_extraction_for_missing_raw_item_returns_404(self) -> None:
        sources = NewsSourceRepository(sources=[])
        app = create_app(settings=_test_settings(), news_source_repository=sources)
        client = TestClient(app)
        response = client.get(
            "/admin/news-sources/raw-items/nonexistent/extraction",
            headers=_admin_headers(),
        )
        assert response.status_code == 404

    def test_extract_missing_raw_item_returns_404(self) -> None:
        sources = NewsSourceRepository(sources=[])
        app = create_app(settings=_test_settings(), news_source_repository=sources)
        client = TestClient(app)
        response = client.post(
            "/admin/news-sources/raw-items/nonexistent/extract",
            headers=_admin_headers(),
        )
        assert response.status_code == 404

    def test_get_extraction_when_not_yet_extracted_returns_404(self) -> None:
        sources, raw, source_id, raw_item_id = _seed_raw_item()
        extracted = ExtractedArticleRepository()
        app = create_app(
            settings=_test_settings(),
            news_source_repository=sources,
            news_raw_item_repository=raw,
            extracted_article_repository=extracted,
        )
        client = TestClient(app)
        # The raw item exists but hasn't been extracted yet
        response = client.get(
            f"/admin/news-sources/raw-items/{raw_item_id}/extraction",
            headers=_admin_headers(),
        )
        assert response.status_code == 404


# ===========================================================================
# Additional: FirecrawlArticleExtractor (unit, with mocks)
# ===========================================================================


class TestFirecrawlArticleExtractor:
    """Tests for FirecrawlArticleExtractor with mocked HTTP."""

    def _setup_urlopen_mock(self, response_body: bytes, monkeypatch=None):
        """Helper to create a proper urlopen mock."""
        class FakeResponse:
            def __init__(self, body):
                self._body = body
            def read(self):
                return self._body
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        return FakeResponse(response_body)

    def test_firecrawl_extracts_successfully(self) -> None:
        raw_item = MagicMock(spec=ParsedFeedItem)
        raw_item.id = "raw_fc"
        raw_item.link_url = "https://example.com/fc"
        raw_item.title = "FC Article"
        raw_item.published_at = datetime.now(UTC)

        response_body = json.dumps({
            "success": True,
            "data": {
                "markdown": "# FC Article\n\nBody text.",
                "metadata": {
                    "title": "FC Article",
                    "sourceURL": "https://example.com/fc",
                    "canonical": "https://example.com/fc",
                    "author": "Author Name",
                    "siteName": "Example Site",
                },
            },
        }).encode("utf-8")

        extractor = FirecrawlArticleExtractor(api_key="sk-test")
        fake_resp = self._setup_urlopen_mock(response_body)
        with patch("backend.app.news_extraction.urlopen", return_value=fake_resp):
            output = extractor.extract(raw_item)

        assert output.title == "FC Article"
        assert output.author == "Author Name"
        assert output.site_name == "Example Site"
        assert output.provider == "firecrawl"
        assert output.content_markdown == "# FC Article\n\nBody text."

    def test_firecrawl_empty_markdown_raises(self) -> None:
        raw_item = MagicMock(spec=ParsedFeedItem)
        raw_item.id = "raw_fc_empty"
        raw_item.link_url = "https://example.com/empty"
        raw_item.title = "Empty"
        raw_item.published_at = None

        response_body = json.dumps({
            "success": True,
            "data": {
                "markdown": "",
                "metadata": {"title": "Empty"},
            },
        }).encode("utf-8")

        extractor = FirecrawlArticleExtractor(api_key="sk-test")
        fake_resp = self._setup_urlopen_mock(response_body)
        with patch("backend.app.news_extraction.urlopen", return_value=fake_resp):
            with pytest.raises(ExtractionError, match="empty markdown"):
                extractor.extract(raw_item)

    def test_firecrawl_missing_data_raises(self) -> None:
        raw_item = MagicMock(spec=ParsedFeedItem)
        raw_item.id = "raw_fc_nodata"
        raw_item.link_url = "https://example.com/nodata"
        raw_item.title = "No Data"
        raw_item.published_at = None

        response_body = json.dumps({
            "success": True,
            "data": None,
        }).encode("utf-8")

        extractor = FirecrawlArticleExtractor(api_key="sk-test")
        fake_resp = self._setup_urlopen_mock(response_body)
        with patch("backend.app.news_extraction.urlopen", return_value=fake_resp):
            with pytest.raises(ExtractionError, match="missing data object"):
                extractor.extract(raw_item)

    def test_firecrawl_http_error_raises(self) -> None:
        from urllib.error import HTTPError

        raw_item = MagicMock(spec=ParsedFeedItem)
        raw_item.id = "raw_fc_http"
        raw_item.link_url = "https://example.com/http"
        raw_item.title = "HTTP Error"
        raw_item.published_at = None

        extractor = FirecrawlArticleExtractor(api_key="sk-test")
        with patch(
            "backend.app.news_extraction.urlopen",
            side_effect=HTTPError(
                url="https://api.firecrawl.dev/v1/scrape",
                code=401,
                msg="Unauthorized",
                hdrs={},
                fp=None,
            ),
        ):
            with pytest.raises(ExtractionError, match="Firecrawl request failed"):
                extractor.extract(raw_item)

    def test_firecrawl_uses_canonical_from_metadata(self) -> None:
        raw_item = MagicMock(spec=ParsedFeedItem)
        raw_item.id = "raw_canon"
        raw_item.link_url = "https://src.com/page"
        raw_item.title = "Canonical"
        raw_item.published_at = None

        response_body = json.dumps({
            "success": True,
            "data": {
                "markdown": "# Canonical\n\nBody.",
                "metadata": {
                    "title": "Canonical",
                    "url": "https://src.com/page",
                    "canonical": "https://canonical.com/page",
                },
            },
        }).encode("utf-8")

        extractor = FirecrawlArticleExtractor(api_key="sk-test")
        fake_resp = self._setup_urlopen_mock(response_body)
        with patch("backend.app.news_extraction.urlopen", return_value=fake_resp):
            output = extractor.extract(raw_item)

        assert output.canonical_url == "https://canonical.com/page"
        assert output.final_url == "https://src.com/page"
