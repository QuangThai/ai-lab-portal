"""Streaming SSE endpoints for all blog pipeline stages.

Extends the blog-ideas router with ``/generate-stream/`` endpoints for
outline, draft, technical review, and marketing. Each follows the same
pattern established by the idea streaming endpoint:

1. Validate the idea exists and pipeline prerequisites are met.
2. Build LLM inputs from the idea (title, outline, draft, context …).
3. Run ``stream_generate()`` with the appropriate prompt + output schema.
4. On ``result``, save the output to the repository.
5. Emit a final ``saved`` event with the redirect URL.
"""

from __future__ import annotations

import json as _json
from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    AdminIdentity,
    require_admin_identity_with_settings,
)
from backend.app.blog_agent_context import build_project_context
from backend.app.blog_ideas import (
    BlogIdea,
    BlogIdeaRepository,
    OutlineSection,
    marketing_metadata_for_storage,
)
from backend.app.llm.schemas import (
    BlogDraft,
    BlogOutline,
    MarketingMetadata,
    TechnicalReview,
)
from backend.app.llm.streaming import stream_generate
from backend.app.settings import Settings
from backend.app.task_support import _build_mcp_servers, ai_run_repository


def _build_streaming_router(
    repository: BlogIdeaRepository,
    settings: Settings,
) -> APIRouter:
    """Return an APIRouter with all /{idea_id}/generate-stream/ endpoints.

    The caller (``create_blog_idea_routes``) mounts these under the same
    ``/admin/blog-ideas`` prefix.
    """
    router = APIRouter()

    def _get_idea(idea_id: str) -> BlogIdea:
        idea = repository.get_by_id(idea_id)
        if idea is None:
            raise HTTPException(status_code=404, detail="Blog idea not found")
        return idea

    # ── Outline streaming ──────────────────────────────────────────────

    @router.post("/{idea_id}/generate-stream/outline")
    async def generate_outline_stream(
        idea_id: str,
        _identity: AdminIdentity = Depends(_make_identity_dep(settings)),
    ) -> StreamingResponse:
        idea = _get_idea(idea_id)
        if idea.status != "approved":
            raise HTTPException(
                status_code=400,
                detail="Outline generation requires an approved idea",
            )

        positioning = (
            ", ".join(idea.positioning_notes) if idea.positioning_notes else ""
        )
        project_context = build_project_context(idea)
        mcp_servers = _build_mcp_servers(settings)

        async def event_stream():
            _result_json: str | None = None

            async for event in stream_generate(
                prompt_name="blog_outline",
                inputs={
                    "title": idea.title,
                    "angle": idea.angle,
                    "target_reader": idea.target_reader,
                    "article_goal": idea.article_goal,
                    "positioning_notes": positioning,
                    "project_context": project_context,
                },
                output_schema=BlogOutline,
                model=settings.llm_model,
                recorder=None,
                entity_id=idea_id,
                entity_type="blog_idea",
                provider="agents_sdk",
                mcp_servers=mcp_servers,
            ):
                if event.startswith('{"type": "result"'):
                    _result_json = event
                yield f"data: {event}\n\n"

            # Save outline to repository
            if _result_json is not None:
                try:
                    parsed = _json.loads(_result_json)
                    result = BlogOutline.model_validate(parsed["data"])
                    sections = [
                        OutlineSection(section=s.section, points=s.points)
                        for s in result.outline
                    ]
                    repository.set_outline(idea_id, sections, status="pending")
                    saved_event = _json.dumps({
                        "type": "saved",
                        "idea_id": idea_id,
                        "redirect_url": f"/admin/blog-ideas/{idea_id}",
                    })
                    yield f"data: {saved_event}\n\n"
                except Exception as exc:
                    err_event = _json.dumps({
                        "type": "error",
                        "data": f"Failed to save outline: {exc}",
                    })
                    yield f"data: {err_event}\n\n"

        return _streaming_response(event_stream())

    # ── Draft streaming ────────────────────────────────────────────────

    @router.post("/{idea_id}/generate-stream/draft")
    async def generate_draft_stream(
        idea_id: str,
        _identity: AdminIdentity = Depends(_make_identity_dep(settings)),
    ) -> StreamingResponse:
        idea = _get_idea(idea_id)
        if idea.outline_status != "approved":
            raise HTTPException(
                status_code=400,
                detail="Draft generation requires an approved outline",
            )

        project_context = build_project_context(idea)
        outline_json = _json.dumps(
            [{"section": s.section, "points": s.points} for s in idea.outline_sections],
            indent=2,
        )
        positioning = (
            ", ".join(idea.positioning_notes) if idea.positioning_notes else "N/A"
        )
        mcp_servers = _build_mcp_servers(settings)

        async def event_stream():
            _result_json: str | None = None

            async for event in stream_generate(
                prompt_name="draft_writer",
                inputs={
                    "outline_json": outline_json,
                    "project_context": project_context,
                    "positioning_notes": positioning,
                },
                output_schema=BlogDraft,
                model=settings.llm_model,
                recorder=None,
                entity_id=idea_id,
                entity_type="blog_idea",
                provider="agents_sdk",
                mcp_servers=mcp_servers,
            ):
                if event.startswith('{"type": "result"'):
                    _result_json = event
                yield f"data: {event}\n\n"

            if _result_json is not None:
                try:
                    parsed = _json.loads(_result_json)
                    result = BlogDraft.model_validate(parsed["data"])
                    repository.set_draft(idea_id, result.markdown, status="pending")
                    saved_event = _json.dumps({
                        "type": "saved",
                        "idea_id": idea_id,
                        "redirect_url": f"/admin/blog-ideas/{idea_id}",
                    })
                    yield f"data: {saved_event}\n\n"
                except Exception as exc:
                    err_event = _json.dumps({
                        "type": "error",
                        "data": f"Failed to save draft: {exc}",
                    })
                    yield f"data: {err_event}\n\n"

        return _streaming_response(event_stream())

    # ── Technical review streaming (with Agent-as-tool ClaimExtractor) ─

    @router.post("/{idea_id}/generate-stream/review")
    async def generate_review_stream(
        idea_id: str,
        _identity: AdminIdentity = Depends(_make_identity_dep(settings)),
    ) -> StreamingResponse:
        idea = _get_idea(idea_id)
        if idea.draft_status != "approved":
            raise HTTPException(
                status_code=400,
                detail="Technical review requires an approved draft",
            )

        project_context = build_project_context(idea)
        mcp_servers = _build_mcp_servers(settings)

        # Build the multi-agent review agent with ClaimExtractor as a tool
        from backend.app.llm.review_agent import build_review_agent

        review_agent = build_review_agent(
            model=settings.llm_model,
            mcp_servers=mcp_servers,
        )

        async def event_stream():
            _result_json: str | None = None

            # User message includes the draft + project context
            user_input = (
                f"Draft to review:\n\n{idea.draft_markdown or ''}\n\n"
                f"Project context:\n\n{project_context}"
            )

            async for event in stream_generate(
                prompt_name="technical_review",
                inputs={"input": user_input},
                output_schema=TechnicalReview,
                model=settings.llm_model,
                recorder=None,
                entity_id=idea_id,
                entity_type="blog_idea",
                provider="agents_sdk",
                agent=review_agent,
            ):
                if event.startswith('{"type": "result"'):
                    _result_json = event
                yield f"data: {event}\n\n"

            if _result_json is not None:
                try:
                    parsed = _json.loads(_result_json)
                    result = TechnicalReview.model_validate(parsed["data"])
                    repository.set_technical_review(
                        idea_id, result.model_dump(), status="pending"
                    )
                    saved_event = _json.dumps({
                        "type": "saved",
                        "idea_id": idea_id,
                        "redirect_url": f"/admin/blog-ideas/{idea_id}",
                    })
                    yield f"data: {saved_event}\n\n"
                except Exception as exc:
                    err_event = _json.dumps({
                        "type": "error",
                        "data": f"Failed to save review: {exc}",
                    })
                    yield f"data: {err_event}\n\n"

        return _streaming_response(event_stream())

    # ── Marketing metadata streaming ───────────────────────────────────

    @router.post("/{idea_id}/generate-stream/marketing")
    async def generate_marketing_stream(
        idea_id: str,
        _identity: AdminIdentity = Depends(_make_identity_dep(settings)),
    ) -> StreamingResponse:
        idea = _get_idea(idea_id)
        if idea.draft_status != "approved":
            raise HTTPException(
                status_code=400,
                detail="Marketing generation requires an approved draft",
            )

        mcp_servers = _build_mcp_servers(settings)

        async def event_stream():
            _result_json: str | None = None

            async for event in stream_generate(
                prompt_name="marketing_metadata",
                inputs={
                    "draft_markdown": idea.draft_markdown or "",
                    "title": idea.title,
                    "angle": idea.angle,
                    "target_reader": idea.target_reader,
                },
                output_schema=MarketingMetadata,
                model=settings.llm_model,
                recorder=None,
                entity_id=idea_id,
                entity_type="blog_idea",
                provider="agents_sdk",
                mcp_servers=mcp_servers,
            ):
                if event.startswith('{"type": "result"'):
                    _result_json = event
                yield f"data: {event}\n\n"

            if _result_json is not None:
                try:
                    parsed = _json.loads(_result_json)
                    result = MarketingMetadata.model_validate(parsed["data"])
                    repository.set_marketing_metadata(
                        idea_id,
                        marketing_metadata_for_storage(result),
                        status="pending",
                    )
                    saved_event = _json.dumps({
                        "type": "saved",
                        "idea_id": idea_id,
                        "redirect_url": f"/admin/blog-ideas/{idea_id}",
                    })
                    yield f"data: {saved_event}\n\n"
                except Exception as exc:
                    err_event = _json.dumps({
                        "type": "error",
                        "data": f"Failed to save marketing metadata: {exc}",
                    })
                    yield f"data: {err_event}\n\n"

        return _streaming_response(event_stream())

    return router


# ── Shared helpers ────────────────────────────────────────────────────


def _make_identity_dep(
    settings: Settings,
) -> Callable[[str | None, str | None], AdminIdentity]:
    """Create a FastAPI dependency that validates admin identity headers."""

    def _dep(
        identity_payload: Annotated[
            str | None, Header(alias=ADMIN_IDENTITY_HEADER)
        ] = None,
        signature: Annotated[
            str | None, Header(alias=ADMIN_SIGNATURE_HEADER)
        ] = None,
    ) -> AdminIdentity:
        return require_admin_identity_with_settings(
            settings, identity_payload, signature
        )

    return _dep


def _streaming_response(generator: Any) -> StreamingResponse:
    """Wrap an async event-stream generator in a standard SSE response."""
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
