"""FastAPI routes for SEO auto-optimization."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
import json

from fastapi import APIRouter, Depends, Header, HTTPException

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    AdminIdentity,
    require_admin_identity_with_settings,
)
from backend.app.blog_ideas import BlogIdeaRepository
from backend.app.seo_optimizer import (
    SeoApplyRequest,
    SeoApplyResult,
    SeoOptimizationResult,
    SeoOptimizerService,
    apply_seo_changes,
)
from backend.app.settings import Settings


def create_seo_optimizer_routes(
    service: SeoOptimizerService,
    ideas_repo: BlogIdeaRepository,
    settings: Settings,
) -> APIRouter:
    def require_admin(
        identity_payload: str | None = Header(default=None, alias=ADMIN_IDENTITY_HEADER),
        signature: str | None = Header(default=None, alias=ADMIN_SIGNATURE_HEADER),
    ) -> AdminIdentity:
        return require_admin_identity_with_settings(settings, identity_payload, signature)

    router = APIRouter(prefix="/admin/blog-ideas", tags=["seo-optimizer"])

    @router.post("/{idea_id}/optimize-seo")
    async def optimize_seo(
        idea_id: str,
        _identity: AdminIdentity = Depends(require_admin),
    ) -> SeoOptimizationResult:
        """Get SEO optimization suggestions for a blog idea."""
        idea = ideas_repo.get_by_id(idea_id)
        if idea is None:
            raise HTTPException(status_code=404, detail="Blog idea not found")

        return service.optimize(
            blog_idea_id=idea_id,
            title=idea.title,
            content_markdown=idea.draft_markdown or "",
            seo_audit=idea.seo_audit,
        )

    @router.post("/{idea_id}/apply-seo-changes")
    async def apply_seo(
        idea_id: str,
        payload: SeoApplyRequest,
        _identity: AdminIdentity = Depends(require_admin),
    ) -> SeoApplyResult:
        """Apply selected SEO changes to a blog idea.

        Accepts a list of section names and the full set of optimization changes.
        Only accepted sections are applied. Returns the new values for the
        frontend to display and confirm before the final save.
        """
        idea = ideas_repo.get_by_id(idea_id)
        if idea is None:
            raise HTTPException(status_code=404, detail="Blog idea not found")

        result = apply_seo_changes(
            idea_title=idea.title,
            draft_markdown=idea.draft_markdown,
            marketing_metadata=idea.marketing_metadata,
            request=payload,
        )

        # Persist changes immediately (admin has already confirmed via accept)
        update_payload: dict[str, Any] = {"updated_at": datetime.now(UTC)}
        if result.new_title is not None:
            update_payload["title"] = result.new_title
        if result.new_draft_markdown is not None:
            update_payload["draft_markdown"] = result.new_draft_markdown
        if result.new_metadata is not None:
            update_payload["marketing_metadata"] = json.dumps(result.new_metadata)

        if len(update_payload) > 1:  # more than just updated_at
            ideas_repo.update_fields(idea_id, update_payload)

        return result

    return router
