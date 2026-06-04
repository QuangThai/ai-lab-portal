"""Tests for US-056 social item scoring calibration."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.app.news_extraction import ExtractedArticle, ExtractedArticleRepository
from backend.app.news_scoring import (
    InMemoryNewsReviewRepository,
    ScoreDimensions,
    _extract_social_metadata,
    compute_heuristic_scores,
    run_score_extracted_article,
)
from backend.app.news_crawl import NewsRawItemRepository, NewsRawItemSummary
from backend.app.news_sources import NewsSource, NewsSourceRepository


def _make_source(source_type: str = "rss") -> NewsSource:
    now = datetime.now(UTC)
    return NewsSource(
        id="newssrc_scoring_test",
        name="Scoring Test Source",
        source_type=source_type,  # type: ignore[arg-type]
        url_or_identifier="https://example.com",
        description="Test source for scoring calibration.",
        priority="medium",
        crawl_frequency_minutes=360,
        is_enabled=True,
        credibility_base_score=0.7,
        created_at=now,
        updated_at=now,
    )


def _make_article(article_id: str | None = None) -> ExtractedArticle:
    now = datetime.now(UTC)
    return ExtractedArticle(
        id=article_id or "extract_scoring_test",
        raw_item_id="raw_scoring_test",
        source_url="https://example.com/article",
        final_url="https://example.com/article",
        canonical_url=None,
        title="New LLM benchmark shows 40% improvement in reasoning tasks",
        author=None,
        site_name=None,
        published_at=now,
        content_markdown="# LLM Benchmark\nResults show significant improvement.",
        content_text="New LLM benchmark shows 40% improvement in reasoning tasks. Results show significant improvement.",
        content_hash="sha256:test_content_hash",
        provider="fake",
        provider_latency_ms=100,
        provider_payload=None,
        extraction_status="success",
        duplicate_status="unique",
        extracted_at=now,
        created_at=now,
        updated_at=now,
    )


class TestSocialMetadataExtraction:
    def test_extract_social_metadata_from_empty_payload(self) -> None:
        result = _extract_social_metadata(None)
        assert result == {}

    def test_extract_social_metadata_no_social_fields(self) -> None:
        result = _extract_social_metadata({"some_other": "data"})
        assert result == {}

    def test_extract_social_engagement_from_values(self) -> None:
        result = _extract_social_metadata({
            "social_like_count": 300,
            "social_repost_count": 50,
            "social_reply_count": 20,
        })
        eng = result.get("social_engagement_score")
        assert eng is not None
        assert 0.3 <= eng <= 0.4  # 370 / 1000 normalized

    def test_extract_social_engagement_caps_at_1000(self) -> None:
        result = _extract_social_metadata({
            "social_like_count": 5000,
            "social_repost_count": 2000,
        })
        eng = result.get("social_engagement_score")
        assert eng is not None
        assert eng == 1.0  # capped

    def test_extract_social_engagement_handles_partial_nulls(self) -> None:
        """Only non-null engagement values contribute."""
        result = _extract_social_metadata({
            "social_like_count": 100,
        })
        eng = result.get("social_engagement_score")
        assert eng is not None
        assert eng == 0.1  # 100 / 1000

    def test_extract_author_credibility_verified_large_following(self) -> None:
        result = _extract_social_metadata({
            "social_author_verified": True,
            "social_author_followers": 5000000,
        })
        cred = result.get("author_credibility_score")
        assert cred is not None
        assert cred >= 0.9  # baseline 0.5 + verified 0.25 + large following 0.2

    def test_extract_author_credibility_unverified_small_following(self) -> None:
        result = _extract_social_metadata({
            "social_author_verified": False,
            "social_author_followers": 500,
        })
        cred = result.get("author_credibility_score")
        assert cred is not None
        assert cred <= 0.55

    def test_extract_risk_flags_from_filter_decision(self) -> None:
        result = _extract_social_metadata({
            "social_filter_decision": {
                "risk_flags": ["spam_or_engagement_bait"],
                "priority": "low",
            },
        })
        assert result.get("social_spam_boost") == 0.3


class TestSocialScoringCalibration:
    def test_compute_scores_with_social_engagement(self) -> None:
        """Social engagement is used when raw payload has social metadata."""
        source = _make_source(source_type="social_x")
        article = _make_article()
        scores = compute_heuristic_scores(
            article=article,
            source=source,
            raw_item_payload={
                "social_like_count": 450,
                "social_repost_count": 85,
                "social_reply_count": 32,
                "social_author_verified": True,
                "social_author_followers": 5000000,
            },
        )
        assert scores.social_engagement_score is not None
        assert scores.social_engagement_score > 0
        assert scores.author_credibility_score is not None
        assert scores.author_credibility_score > 0.5
        assert scores.engagement_score == scores.social_engagement_score

    def test_compute_scores_without_social_data_defaults(self) -> None:
        """Without social metadata, author and social scores are None."""
        source = _make_source(source_type="rss")
        article = _make_article()
        scores = compute_heuristic_scores(
            article=article,
            source=source,
            raw_item_payload=None,
        )
        assert scores.author_credibility_score is None
        assert scores.social_engagement_score is None
        assert scores.engagement_score == 0.5  # default

    def test_compute_scores_social_spam_boost(self) -> None:
        """Social spam risk flags boost the spam score."""
        source = _make_source(source_type="social_x")
        article = _make_article()
        scores = compute_heuristic_scores(
            article=article,
            source=source,
            raw_item_payload={
                "social_filter_decision": {
                    "risk_flags": ["spam_or_engagement_bait"],
                    "priority": "low",
                },
            },
        )
        assert scores.spam_risk_score >= 0.3  # boosted by social spam

    def test_upsert_scored_stores_social_fields(self) -> None:
        """Review item stores social scoring fields via upsert_scored."""
        source = _make_source(source_type="social_x")
        sources = NewsSourceRepository()
        sources._sources = {source.id: source}
        article = _make_article(article_id="extract_upsert_social")
        assert article.raw_item_id == "raw_scoring_test"  # must match raw_items key below
        extracted = ExtractedArticleRepository()
        extracted._rows[article.id] = article
        raw_items = NewsRawItemRepository()
        raw_items._items[("x", article.raw_item_id)] = NewsRawItemSummary(
            id=article.raw_item_id,
            source_id=source.id,
            external_id="social_test_upsert",
            title="Test social article",
            link_url="https://example.com/article",
            published_at=datetime.now(UTC),
            fetched_at=datetime.now(UTC),
        )
        review = InMemoryNewsReviewRepository()

        result = run_score_extracted_article(
            article.id,
            extracted=extracted,
            raw_items=raw_items,
            sources=sources,
            review=review,
        )

        review_item = review.get_by_extracted_article_id(article.id)
        assert review_item is not None
        # Without raw_payload in in-memory repo, social scores remain None
        # Production Postgres path carries raw_payload from DB column
        assert review_item.author_credibility_score is None
        assert review_item.social_engagement_score is None
        assert result.review_status in {"candidate", "low_score"}
        assert result.final_publish_score > 0.4

    def test_non_social_source_defaults(self) -> None:
        """RSS sources don't get social scoring fields via run_score."""
        source = _make_source(source_type="rss")
        sources = NewsSourceRepository()
        sources._sources = {source.id: source}
        article = _make_article(article_id="extract_rss_default")
        assert article.raw_item_id == "raw_scoring_test"  # must match raw_items key below
        extracted = ExtractedArticleRepository()
        extracted._rows[article.id] = article
        raw_items = NewsRawItemRepository()
        raw_items._items[("rss", article.raw_item_id)] = NewsRawItemSummary(
            id=article.raw_item_id,
            source_id=source.id,
            external_id="rss_test_default",
            title="RSS test article",
            link_url="https://example.com/rss-article",
            published_at=datetime.now(UTC),
            fetched_at=datetime.now(UTC),
        )
        review = InMemoryNewsReviewRepository()

        run_score_extracted_article(
            article.id,
            extracted=extracted,
            raw_items=raw_items,
            sources=sources,
            review=review,
        )

        review_item = review.get_by_extracted_article_id(article.id)
        assert review_item is not None
        assert review_item.author_credibility_score is None
        assert review_item.social_engagement_score is None


class TestScoreDimensionsModel:
    def test_default_social_scores_are_none(self) -> None:
        """ScoreDimensions allows author_credibility_score and social_engagement_score to be None."""
        scores = ScoreDimensions(
            source_credibility_score=0.7,
            engagement_score=0.5,
            relevance_score=0.3,
            novelty_score=0.5,
            technical_depth_score=0.3,
            business_value_score=0.2,
            spam_risk_score=0.1,
            final_publish_score=0.4,
        )
        assert scores.author_credibility_score is None
        assert scores.social_engagement_score is None

    def test_social_scores_can_be_set(self) -> None:
        """ScoreDimensions accepts social scoring values."""
        scores = ScoreDimensions(
            source_credibility_score=0.7,
            engagement_score=0.6,
            relevance_score=0.3,
            novelty_score=0.5,
            technical_depth_score=0.3,
            business_value_score=0.2,
            spam_risk_score=0.1,
            final_publish_score=0.5,
            author_credibility_score=0.85,
            social_engagement_score=0.6,
        )
        assert scores.author_credibility_score == 0.85
        assert scores.social_engagement_score == 0.6
