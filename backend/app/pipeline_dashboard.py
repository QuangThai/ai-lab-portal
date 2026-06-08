"""Pipeline Dashboard API — aggregate pipeline metrics and visualisation data.

Exposes:
- ``GET /admin/pipeline-dashboard/overview`` — aggregate metrics
- ``GET /admin/pipeline-dashboard/ideas`` — per-idea stage details

Mounted by ``create_app()`` under the default FastAPI app.
"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Header

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    AdminIdentity,
    require_admin_identity_with_settings,
)
from backend.app.blog import BlogRepository
from backend.app.blog_ideas import BlogIdea, BlogIdeaRepository
from backend.app.settings import Settings


STAGE_ORDER = [
    "idea",
    "approved",
    "outline_done",
    "draft_done",
    "reviewed",
    "marketing_done",
    "seo_done",
    "published",
]

STAGE_LABELS: dict[str, str] = {
    "idea": "Idea",
    "approved": "Approved",
    "outline_done": "Outline",
    "draft_done": "Draft",
    "reviewed": "Reviewed",
    "marketing_done": "Marketing",
    "seo_done": "SEO",
    "published": "Published",
}

STAGE_COLORS: dict[str, str] = {
    "idea": "#94a3b8",
    "approved": "#f59e0b",
    "outline_done": "#8b5cf6",
    "draft_done": "#f97316",
    "reviewed": "#06b6d4",
    "marketing_done": "#3b82f6",
    "seo_done": "#10b981",
    "published": "#22c55e",
}


def _idea_stage(idea: BlogIdea) -> str:
    """Determine the current pipeline stage of a blog idea."""
    if idea.published_blog_post_id:
        return "published"
    if idea.seo_audit_status == "approved":
        return "seo_done"
    if idea.marketing_status == "approved":
        return "marketing_done"
    if idea.technical_review_status == "approved":
        return "reviewed"
    if idea.draft_status == "approved":
        return "draft_done"
    if idea.outline_status == "approved":
        return "outline_done"
    if idea.status == "approved":
        return "approved"
    return "idea"


def _stage_order(stage: str) -> int:
    try:
        return STAGE_ORDER.index(stage)
    except ValueError:
        return len(STAGE_ORDER)


def create_pipeline_dashboard_routes(
    settings: Settings,
    blog_idea_repository: BlogIdeaRepository | None = None,
    blog_repository: BlogRepository | None = None,
) -> APIRouter:
    """Create a router with pipeline dashboard endpoints."""

    def require_identity(
        identity_payload: str | None = Header(None, alias=ADMIN_IDENTITY_HEADER),
        signature: str | None = Header(None, alias=ADMIN_SIGNATURE_HEADER),
    ) -> AdminIdentity:
        return require_admin_identity_with_settings(
            settings, identity_payload, signature
        )

    router = APIRouter(prefix="/admin/pipeline-dashboard")

    @router.get("/overview")
    async def get_overview(
        _identity: AdminIdentity = Depends(require_identity),
    ) -> dict[str, Any]:
        """Return aggregate pipeline metrics for the dashboard."""
        ideas_repo = blog_idea_repository or BlogIdeaRepository()
        blog_repo = blog_repository or BlogRepository()

        all_ideas = list(ideas_repo.list_all())

        # Stage distribution
        stage_counts: dict[str, int] = {}
        for idea_obj in all_ideas:
            stage = _idea_stage(idea_obj)
            stage_counts[stage] = stage_counts.get(stage, 0) + 1

        # Sort stages by pipeline order
        sorted_stages = [
            {"stage": s, "label": STAGE_LABELS.get(s, s), "count": stage_counts.get(s, 0), "color": STAGE_COLORS.get(s, "#94a3b8")}
            for s in STAGE_ORDER
            if stage_counts.get(s, 0) > 0
        ]

        # Stage queues — detailed items at each stage
        stage_queues: dict[str, list[dict[str, Any]]] = {}
        for idea_obj in all_ideas:
            stage = _idea_stage(idea_obj)
            if stage not in stage_queues:
                stage_queues[stage] = []
            stage_queues[stage].append({
                "id": idea_obj.id,
                "title": idea_obj.title,
                "stage": stage,
                "created_at": idea_obj.created_at.isoformat() if idea_obj.created_at else None,
            })

        # Published count (for throughput)
        all_posts = blog_repo.list_all()
        published_posts = [p for p in all_posts if p.status == "published"]

        # Count published by month for throughput trend
        monthly_throughput: dict[str, int] = {}
        for p in published_posts:
            if p.published_at:
                key = p.published_at.strftime("%Y-%m")
                monthly_throughput[key] = monthly_throughput.get(key, 0) + 1

        # Count ideas created by month
        monthly_created: dict[str, int] = {}
        for idea_obj in all_ideas:
            if idea_obj.created_at:
                key = idea_obj.created_at.strftime("%Y-%m")
                monthly_created[key] = monthly_created.get(key, 0) + 1

        # Cycle time estimation (time from idea creation to publish)
        cycle_times: list[int] = []
        for idea_obj in all_ideas:
            if idea_obj.published_blog_post_id and idea_obj.created_at:
                # Find the published post to get publish date
                for p in published_posts:
                    if p.id == idea_obj.published_blog_post_id and p.published_at:
                        delta = p.published_at - idea_obj.created_at
                        cycle_times.append(int(delta.total_seconds() / 86400))  # days
                        break

        avg_cycle_time = round(sum(cycle_times) / len(cycle_times), 1) if cycle_times else 0
        max_cycle_time = max(cycle_times) if cycle_times else 0
        min_cycle_time = min(cycle_times) if cycle_times else 0

        # Total in pipeline (excl. published/rejected)
        in_pipeline = sum(
            1 for idea_obj in all_ideas
            if _idea_stage(idea_obj) != "published" and idea_obj.status != "rejected"
        )

        return {
            "total_ideas": len(all_ideas),
            "in_pipeline": in_pipeline,
            "published_count": len(published_posts),
            "rejected_count": sum(1 for i in all_ideas if i.status == "rejected"),
            "stage_distribution": sorted_stages,
            "stage_queues": stage_queues,
            "monthly_throughput": monthly_throughput,
            "monthly_created": monthly_created,
            "cycle_time": {
                "avg_days": avg_cycle_time,
                "min_days": min_cycle_time,
                "max_days": max_cycle_time,
            },
        }

    @router.get("/ideas")
    async def list_pipeline_ideas(
        _identity: AdminIdentity = Depends(require_identity),
    ) -> list[dict[str, Any]]:
        """Return all ideas with stage info for the Gantt-like view."""
        ideas_repo = blog_idea_repository or BlogIdeaRepository()

        all_ideas = list(ideas_repo.list_all())
        results: list[dict[str, Any]] = []

        for idea_obj in all_ideas:
            stage = _idea_stage(idea_obj)
            results.append({
                "id": idea_obj.id,
                "title": idea_obj.title,
                "stage": stage,
                "stage_label": STAGE_LABELS.get(stage, stage),
                "stage_order": _stage_order(stage),
                "status": idea_obj.status,
                "created_at": idea_obj.created_at.isoformat() if idea_obj.created_at else None,
                "scheduled_at": idea_obj.scheduled_at.isoformat() if idea_obj.scheduled_at else None,
                "outline_status": idea_obj.outline_status,
                "draft_status": idea_obj.draft_status,
                "review_status": idea_obj.technical_review_status,
                "marketing_status": idea_obj.marketing_status,
                "seo_status": idea_obj.seo_audit_status,
                "published_post_id": idea_obj.published_blog_post_id,
            })

        results.sort(key=lambda i: (i["stage_order"], i["created_at"] or ""))
        return results

    return router
