"""Shared helpers for Celery tasks (LLM recording, generation job status)."""

from __future__ import annotations

from backend.app.ai_runs import AiRunRepository, PostgresAiRunRepository
from backend.app.blog_ideas import BlogIdeaRepository, PostgresBlogIdeaRepository
from backend.app.database import create_database_engine
from backend.app.generation_jobs import (
    GenerationJobRepository,
    PostgresGenerationJobRepository,
)
from backend.app.llm.recording import RecordingLLMService
from backend.app.llm.service import LLMService, OpenAILLMService


_RESOLVED_AGENTS_SDK: bool | None = None


def _use_agents_sdk(settings: Settings) -> bool:
    """Check whether the Agents SDK backend is configured."""
    return settings.llm_backend == "agents_sdk"
from backend.app.news_crawl import NewsRawItemRepository, PostgresNewsRawItemRepository
from backend.app.news_extraction import (
    ExtractedArticleRepository,
    PostgresExtractedArticleRepository,
    extractor_for_settings,
)
from backend.app.news_sources import NewsSourceRepository, PostgresNewsSourceRepository
from backend.app.news_scoring import (
    InMemoryNewsReviewRepository,
    PostgresNewsReviewRepository,
    NewsReviewRepository,
)
from backend.app.news_submitted_links import (
    InMemorySubmittedLinkRepository,
    PostgresSubmittedLinkRepository,
    SubmittedLinkRepository,
)
from backend.app.settings import Settings


def news_source_repository(settings: Settings | None = None) -> NewsSourceRepository:
    resolved = settings or Settings()
    if resolved.environment == "test":
        return NewsSourceRepository()
    return PostgresNewsSourceRepository(create_database_engine(resolved))


def news_raw_item_repository(settings: Settings | None = None) -> NewsRawItemRepository:
    resolved = settings or Settings()
    if resolved.environment == "test":
        return NewsRawItemRepository()
    return PostgresNewsRawItemRepository(create_database_engine(resolved))


def extracted_article_repository(
    settings: Settings | None = None,
) -> ExtractedArticleRepository:
    resolved = settings or Settings()
    if resolved.environment == "test":
        return ExtractedArticleRepository()
    return PostgresExtractedArticleRepository(create_database_engine(resolved))


def article_extractor(settings: Settings | None = None):
    return extractor_for_settings(settings or Settings())


def news_review_repository(settings: Settings | None = None) -> NewsReviewRepository:
    resolved = settings or Settings()
    if resolved.environment == "test":
        return InMemoryNewsReviewRepository()
    return PostgresNewsReviewRepository(create_database_engine(resolved))


def submitted_link_repository(settings: Settings | None = None) -> SubmittedLinkRepository:
    resolved = settings or Settings()
    if resolved.environment == "test":
        return InMemorySubmittedLinkRepository()
    return PostgresSubmittedLinkRepository(create_database_engine(resolved))


def idea_repository(settings: Settings | None = None) -> BlogIdeaRepository:
    resolved = settings or Settings()
    if resolved.environment == "test":
        return BlogIdeaRepository()
    return PostgresBlogIdeaRepository(create_database_engine(resolved))


def ai_run_repository(settings: Settings | None = None) -> AiRunRepository | None:
    resolved = settings or Settings()
    if resolved.environment == "test":
        return AiRunRepository()
    return PostgresAiRunRepository(create_database_engine(resolved))


def generation_job_repository(
    settings: Settings | None = None,
) -> GenerationJobRepository:
    resolved = settings or Settings()
    if resolved.environment == "test":
        return GenerationJobRepository()
    return PostgresGenerationJobRepository(create_database_engine(resolved))


def _build_llm_service(
    api_key: str,
    model: str,
    settings: Settings,
    entity_id: str | None = None,
) -> LLMService:
    """Create the configured LLM service based on AI_LAB_LLM_BACKEND."""
    if _use_agents_sdk(settings):
        from backend.app.llm.agents_sdk_service import AgentsSDKLLMService
        from backend.app.llm.sessions import get_session_store

        return AgentsSDKLLMService(
            api_key=api_key,
            model=model,
            session_store=get_session_store(),
            entity_id=entity_id,
        )
    return OpenAILLMService(api_key=api_key, model=model)


def _register_blog_guardrails(
    service: LLMService,
    idea_id: str,
    settings: Settings,
) -> None:
    """Register guardrails for blog idea pipeline stages."""
    if not _use_agents_sdk(settings):
        return
    from backend.app.llm.agents_sdk_service import AgentsSDKLLMService

    if not isinstance(service, AgentsSDKLLMService):
        return

    from backend.app.llm.guardrails import claim_extraction_guardrail
    from backend.app.task_support import idea_repository
    from backend.app.blog_claims import BlogClaimsRepository

    # Register claim extraction guardrail on technical review
    ideas_repo = idea_repository(settings)
    claims_repo = BlogClaimsRepository()
    guardrail = claim_extraction_guardrail(claims_repo, ideas_repo)
    service.add_guardrail("technical_review", guardrail)


def _provider_name(settings: Settings) -> str:
    return "agents_sdk" if _use_agents_sdk(settings) else "openai"


def llm_service_for_news_item(
    review_entity_id: str,
    settings: Settings | None = None,
) -> LLMService | None:
    resolved = settings or Settings()
    api_key = resolved.llm_openai_api_key.get_secret_value()
    if not api_key:
        return None
    inner = _build_llm_service(api_key, resolved.llm_model, resolved)
    recorder = ai_run_repository(resolved)
    if recorder is None:
        return inner
    return RecordingLLMService(
        inner,
        recorder,
        entity_type="ai_news_scoring",
        entity_id=review_entity_id,
        provider=_provider_name(resolved),
        model=resolved.llm_model,
    )


def llm_service_for_idea(
    idea_id: str,
    settings: Settings | None = None,
) -> LLMService:
    resolved = settings or Settings()
    if resolved.llm_e2e_fake:
        from backend.app.llm.e2e_fake_responses import build_e2e_fake_llm_service

        inner = build_e2e_fake_llm_service()
        recorder = ai_run_repository(resolved)
        if recorder is None:
            return inner
        return RecordingLLMService(
            inner,
            recorder,
            entity_type="blog_idea",
            entity_id=idea_id,
            provider="e2e_fake",
            model="e2e_fake",
        )
    api_key = resolved.llm_openai_api_key.get_secret_value()
    if not api_key:
        raise RuntimeError(
            "AI_LAB_LLM_OPENAI_API_KEY is not set. "
            "Add it to .env or the process environment."
        )
    inner = _build_llm_service(
        api_key, resolved.llm_model, resolved, entity_id=idea_id
    )
    _register_blog_guardrails(inner, idea_id, resolved)
    recorder = ai_run_repository(resolved)
    if recorder is None:
        return inner
    return RecordingLLMService(
        inner,
        recorder,
        entity_type="blog_idea",
        entity_id=idea_id,
        provider=_provider_name(resolved),
        model=resolved.llm_model,
    )


def track_job_lifecycle(task) -> GenerationJobRepository:
    """Mark a Celery task running; caller should complete/fail on exit."""
    jobs = generation_job_repository()
    jobs.mark_running(task.request.id)
    return jobs
