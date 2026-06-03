"""Celery tasks for the AI Lab Portal.

Tasks defined here are auto-discovered by ``celery_app`` via the
``include=["backend.app.tasks"]`` config.
"""

import json

from backend.app.blog_ideas import (
    BlogIdeaCreate,
    BlogIdeaRepository,
    OutlineSection,
    PostgresBlogIdeaRepository,
)
from backend.app.celery_app import celery_app
from backend.app.database import create_database_engine
from backend.app.llm.schemas import BlogDraft
from backend.app.llm.schemas import BlogIdea as BlogIdeaSchema
from backend.app.llm.schemas import BlogOutline
from backend.app.llm.schemas import MarketingMetadata
from backend.app.llm.schemas import TechnicalReview
from backend.app.llm.service import OpenAILLMService
from backend.app.settings import Settings


def _llm_service() -> OpenAILLMService:
    settings = Settings()
    api_key = settings.llm_openai_api_key.get_secret_value()
    if not api_key:
        raise RuntimeError(
            "AI_LAB_LLM_OPENAI_API_KEY is not set. "
            "Add it to .env or the process environment."
        )
    return OpenAILLMService(api_key=api_key, model=settings.llm_model)


def _repository() -> BlogIdeaRepository:
    settings = Settings()
    if settings.environment == "test":
        return BlogIdeaRepository()
    engine = create_database_engine(settings)
    return PostgresBlogIdeaRepository(engine)


@celery_app.task(name="foundation.smoke")
def foundation_smoke() -> dict[str, str]:
    return {"status": "ok", "task": "foundation.smoke"}


@celery_app.task(name="blog_ideas.generate", bind=True, max_retries=2)
def generate_blog_idea_task(
    self,
    project_name: str,
    project_summary: str,
    ai_capabilities: str = "",
    technical_highlights: str = "",
    business_value: str = "",
) -> dict:
    """Generate a blog idea from project context using the LLM service."""
    service = _llm_service()
    try:
        result = service.generate(
            "blog_idea",
            inputs={
                "project_name": project_name,
                "project_summary": project_summary,
                "ai_capabilities": ai_capabilities,
                "technical_highlights": technical_highlights,
                "business_value": business_value,
            },
            output_schema=BlogIdeaSchema,
        )
    except Exception as exc:
        raise self.retry(exc=exc)

    # Store in repository
    repo = _repository()
    idea = repo.add_generated(
        BlogIdeaCreate(
            title=result.title,
            angle=result.angle,
            target_reader=result.target_reader,
            article_goal=result.article_goal,
            positioning_notes=result.positioning_notes,
        ),
        context={
            "project_name": project_name,
            "project_summary": project_summary,
        },
    )
    return idea.model_dump()


@celery_app.task(name="blog_ideas.generate_outline", bind=True, max_retries=2)
def generate_blog_outline_task(
    self,
    idea_id: str,
) -> dict:
    """Generate an outline for an approved blog idea.

    Fetches the idea from the repository, calls the LLM service with the
    ``blog_outline`` prompt, and stores the result back.
    """
    repo = _repository()
    idea = repo.get_by_id(idea_id)
    if idea is None:
        raise ValueError(f"Blog idea {idea_id} not found")
    if idea.status != "approved":
        raise ValueError(f"Blog idea {idea_id} is not approved (status={idea.status})")

    positioning_text = (
        ", ".join(idea.positioning_notes) if idea.positioning_notes else ""
    )

    service = _llm_service()
    try:
        result = service.generate(
            "blog_outline",
            inputs={
                "title": idea.title,
                "angle": idea.angle,
                "target_reader": idea.target_reader,
                "article_goal": idea.article_goal,
                "positioning_notes": positioning_text,
            },
            output_schema=BlogOutline,
        )
    except Exception as exc:
        raise self.retry(exc=exc)

    sections = [
        OutlineSection(section=s.section, points=s.points)
        for s in result.outline
    ]
    updated = repo.set_outline(idea_id, sections, status="pending")
    if updated is None:
        raise RuntimeError(f"Failed to store outline for idea {idea_id}")

    return updated.model_dump()


@celery_app.task(name="blog_ideas.generate_draft", bind=True, max_retries=2)
def generate_blog_draft_task(
    self,
    idea_id: str,
) -> dict:
    """Generate a full markdown draft from an approved outline."""
    repo = _repository()
    idea = repo.get_by_id(idea_id)
    if idea is None:
        raise ValueError(f"Blog idea {idea_id} not found")
    if idea.outline_status != "approved":
        raise ValueError(
            f"Blog idea {idea_id} outline is not approved "
            f"(status={idea.outline_status})"
        )

    # Build project context summary
    context_parts = [
        f"Title: {idea.title}",
        f"Angle: {idea.angle}",
        f"Target reader: {idea.target_reader}",
        f"Article goal: {idea.article_goal}",
    ]
    if idea.positioning_notes:
        context_parts.append(
            f"Positioning notes: {', '.join(idea.positioning_notes)}"
        )
    project_context = "\n".join(context_parts)

    outline_json = json.dumps(
        [
            {"section": s.section, "points": s.points}
            for s in idea.outline_sections
        ],
        indent=2,
    )
    positioning = (
        ", ".join(idea.positioning_notes) if idea.positioning_notes else "N/A"
    )

    service = _llm_service()
    try:
        result = service.generate(
            "draft_writer",
            inputs={
                "outline_json": outline_json,
                "project_context": project_context,
                "positioning_notes": positioning,
            },
            output_schema=BlogDraft,
        )
    except Exception as exc:
        raise self.retry(exc=exc)

    updated = repo.set_draft(idea_id, result.markdown, status="pending")
    if updated is None:
        raise RuntimeError(f"Failed to store draft for idea {idea_id}")

    return updated.model_dump()


@celery_app.task(name="blog_ideas.review_technical", bind=True, max_retries=2)
def generate_technical_review_task(
    self,
    idea_id: str,
) -> dict:
    """Run AI technical review on an approved draft."""
    repo = _repository()
    idea = repo.get_by_id(idea_id)
    if idea is None:
        raise ValueError(f"Blog idea {idea_id} not found")
    if idea.draft_status != "approved":
        raise ValueError(
            f"Blog idea {idea_id} draft is not approved "
            f"(status={idea.draft_status})"
        )

    project_context_parts = [
        f"Title: {idea.title}",
        f"Angle: {idea.angle}",
        f"Target reader: {idea.target_reader}",
        f"Article goal: {idea.article_goal}",
    ]
    if idea.positioning_notes:
        project_context_parts.append(
            f"Positioning notes: {', '.join(idea.positioning_notes)}"
        )
    project_context = "\n".join(project_context_parts)

    service = _llm_service()
    try:
        result = service.generate(
            "technical_review",
            inputs={
                "draft_markdown": idea.draft_markdown or "",
                "project_context": project_context,
            },
            output_schema=TechnicalReview,
        )
    except Exception as exc:
        raise self.retry(exc=exc)

    review_data = result.model_dump()
    updated = repo.set_technical_review(idea_id, review_data, status="pending")
    if updated is None:
        raise RuntimeError(f"Failed to store technical review for idea {idea_id}")

    return updated.model_dump()


@celery_app.task(name="blog_ideas.generate_marketing", bind=True, max_retries=2)
def generate_marketing_metadata_task(
    self,
    idea_id: str,
) -> dict:
    """Generate SEO metadata and social snippets from an approved draft."""
    repo = _repository()
    idea = repo.get_by_id(idea_id)
    if idea is None:
        raise ValueError(f"Blog idea {idea_id} not found")
    if idea.draft_status != "approved":
        raise ValueError(
            f"Blog idea {idea_id} draft is not approved "
            f"(status={idea.draft_status})"
        )

    service = _llm_service()
    try:
        result = service.generate(
            "marketing_metadata",
            inputs={
                "draft_markdown": idea.draft_markdown or "",
                "title": idea.title,
                "angle": idea.angle,
                "target_reader": idea.target_reader,
            },
            output_schema=MarketingMetadata,
        )
    except Exception as exc:
        raise self.retry(exc=exc)

    metadata_data = result.model_dump()
    updated = repo.set_marketing_metadata(idea_id, metadata_data, status="pending")
    if updated is None:
        raise RuntimeError(
            f"Failed to store marketing metadata for idea {idea_id}"
        )

    return updated.model_dump()
