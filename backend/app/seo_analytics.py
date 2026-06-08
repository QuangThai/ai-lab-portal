"""SEO Analytics API — blog post performance, SEO audit, and keyword analysis.

Exposes:
- ``GET /admin/seo-analytics/stats`` — aggregate metrics
- ``GET /admin/seo-analytics/posts`` — per-post SEO analysis
- ``GET /admin/seo-analytics/keywords`` — tag/keyword frequency

Mounted by ``create_app()`` under the default FastAPI app.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, Query

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    AdminIdentity,
    require_admin_identity_with_settings,
)
from backend.app.blog import BlogRepository
from backend.app.blog_ideas import BlogIdeaRepository
from backend.app.blog_tags import BlogTagRepository
from backend.app.settings import Settings

# ── SEO analysis helpers ────────────────────────────────────────────


def _analyze_seo(metadata: dict[str, Any] | None) -> dict[str, Any]:
    """Analyze marketing metadata for SEO quality.

    Returns a dict with score (0-100), issues list, and details.
    """
    if not metadata:
        return {"score": 0, "issues": ["No marketing metadata"], "details": {}}

    issues: list[str] = []
    score = 100

    seo_title = str(metadata.get("seo_title", "") or "")
    meta_desc = str(metadata.get("meta_description", "") or "")
    keywords = metadata.get("keywords", [])

    # SEO title check
    title_len = len(seo_title)
    if title_len == 0:
        issues.append("Missing SEO title (-30)")
        score -= 30
    elif title_len > 60:
        issues.append(f"SEO title too long ({title_len}/60 chars, -10)")
        score -= 10
    elif title_len < 20:
        issues.append(f"SEO title too short ({title_len}/20 chars, -5)")
        score -= 5

    # Meta description check
    desc_len = len(meta_desc)
    if desc_len == 0:
        issues.append("Missing meta description (-25)")
        score -= 25
    elif desc_len > 160:
        issues.append(f"Meta description too long ({desc_len}/160 chars, -10)")
        score -= 10
    elif desc_len < 50:
        issues.append(f"Meta description too short ({desc_len}/50 chars, -5)")
        score -= 5

    # Keywords check
    if not keywords or (isinstance(keywords, list) and len(keywords) == 0):
        issues.append("No keywords defined (-10)")
        score -= 10
    elif isinstance(keywords, list) and len(keywords) > 5:
        issues.append(f"Too many keywords ({len(keywords)}/5 max, -5)")
        score -= 5

    return {
        "score": max(0, score),
        "issues": issues,
        "details": {
            "seo_title_length": title_len,
            "meta_description_length": desc_len,
            "keyword_count": len(keywords) if isinstance(keywords, list) else 0,
        },
    }


def _publish_month_key(dt: datetime | None) -> str:
    """Return 'YYYY-MM' from a datetime, or 'unknown'."""
    if dt is None:
        return "unknown"
    return dt.strftime("%Y-%m")


# ── Router factory ─────────────────────────────────────────────────


def create_seo_analytics_routes(
    settings: Settings,
    blog_repository: BlogRepository | None = None,
    blog_idea_repository: BlogIdeaRepository | None = None,
    blog_tag_repository: BlogTagRepository | None = None,
) -> APIRouter:
    """Create a router with SEO analytics endpoints."""

    def require_identity(
        identity_payload: str | None = Header(None, alias=ADMIN_IDENTITY_HEADER),
        signature: str | None = Header(None, alias=ADMIN_SIGNATURE_HEADER),
    ) -> AdminIdentity:
        return require_admin_identity_with_settings(
            settings, identity_payload, signature
        )

    router = APIRouter(prefix="/admin/seo-analytics")

    @router.get("/stats")
    async def get_stats(
        _identity: AdminIdentity = Depends(require_identity),
    ) -> dict:
        """Return aggregate SEO and post performance statistics."""
        blog_repo = blog_repository or BlogRepository()
        ideas_repo = blog_idea_repository or BlogIdeaRepository()
        tags_repo = blog_tag_repository or BlogTagRepository()

        # Get all posts
        all_posts = blog_repo.list_all()
        published = [p for p in all_posts if p.status == "published"]
        published.sort(key=lambda p: p.published_at or datetime.min.replace(tzinfo=UTC))

        # Get all blog ideas with marketing metadata
        all_ideas = list(ideas_repo.list_all())

        # Publish trend
        publish_trend: dict[str, int] = {}
        for post in published:
            key = _publish_month_key(post.published_at)
            publish_trend[key] = publish_trend.get(key, 0) + 1

        # SEO analysis on ideas with marketing metadata
        seo_scores: list[int] = []
        total_issues = 0
        posts_needing_attention: list[dict] = []
        for idea in all_ideas:
            if idea.marketing_metadata:
                analysis = _analyze_seo(idea.marketing_metadata)
                seo_scores.append(analysis["score"])
                total_issues += len(analysis["issues"])
                if score := analysis["score"] < 70:
                    posts_needing_attention.append({
                        "id": idea.id,
                        "title": idea.title,
                        "seo_score": analysis["score"],
                        "issues": analysis["issues"],
                    })

        # Tags
        all_tags = tags_repo.list_admin_tags()
        published_post_ids = {p.id for p in published}

        avg_seo = (
            round(sum(seo_scores) / len(seo_scores), 1) if seo_scores else 0.0
        )

        return {
            "total_posts": len(all_posts),
            "published_posts": len(published),
            "draft_posts": len(all_posts) - len(published),
            "ideas_with_seo": len(seo_scores),
            "avg_seo_score": avg_seo,
            "total_seo_issues": total_issues,
            "posts_needing_attention": len(posts_needing_attention),
            "publish_trend": publish_trend,
            "tags": len(all_tags),
        }

    @router.get("/posts")
    async def list_post_analysis(
        limit: int = Query(default=50, ge=1, le=200),
        min_score: int | None = Query(
            default=None, ge=0, le=100,
            description="Filter to posts with SEO score below this threshold",
        ),
        _identity: AdminIdentity = Depends(require_identity),
    ) -> list[dict]:
        """Return per-post SEO analysis, sorted by SEO score ascending."""
        blog_repo = blog_repository or BlogRepository()
        ideas_repo = blog_idea_repository or BlogIdeaRepository()

        all_posts = blog_repo.list_all()
        all_ideas = list(ideas_repo.list_all())

        # Map ideas to their posts via published_blog_post_id
        idea_by_post_id = {
            idea.published_blog_post_id: idea
            for idea in all_ideas
            if idea.published_blog_post_id
        }

        results: list[dict] = []
        for post in all_posts:
            idea = idea_by_post_id.get(post.id)
            metadata = idea.marketing_metadata if idea else None
            analysis = _analyze_seo(metadata)

            if min_score is not None and analysis["score"] >= min_score:
                continue

            results.append({
                "post_id": post.id,
                "title": post.title,
                "slug": post.slug,
                "status": post.status,
                "published_at": (
                    post.published_at.isoformat() if post.published_at else None
                ),
                "seo_score": analysis["score"],
                "issues": analysis["issues"],
                "seo_details": analysis["details"],
                "has_marketing_metadata": metadata is not None,
            })

        results.sort(key=lambda r: r["seo_score"])
        return results[:limit]

    @router.get("/keywords")
    async def list_keywords(
        _identity: AdminIdentity = Depends(require_identity),
    ) -> list[dict]:
        """Return keyword/tag frequency analysis."""
        tags_repo = blog_tag_repository or BlogTagRepository()
        ideas_repo = blog_idea_repository or BlogIdeaRepository()

        # Tag frequency from the tags system
        all_tags = tags_repo.list_admin_tags()
        tags_with_counts = [
            {"name": t.name, "count": t.post_count, "type": "tag"}
            for t in all_tags
            if t.post_count > 0
        ]

        # Keywords from marketing metadata
        all_ideas = list(ideas_repo.list_all())
        keyword_counts: dict[str, int] = {}
        for idea in all_ideas:
            if idea.marketing_metadata:
                keywords = idea.marketing_metadata.get("keywords", [])
                if isinstance(keywords, list):
                    for kw in keywords:
                        keyword_counts[str(kw).lower().strip()] = (
                            keyword_counts.get(str(kw).lower().strip(), 0) + 1
                        )

        keyword_items = [
            {"name": k, "count": v, "type": "keyword"}
            for k, v in sorted(keyword_counts.items(), key=lambda x: -x[1])
        ]

        # Merge and sort
        all_items = tags_with_counts + keyword_items
        all_items.sort(key=lambda x: -x["count"])
        return all_items[:50]

    return router
