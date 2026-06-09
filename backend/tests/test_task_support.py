"""Tests for task_support — shared helpers for Celery tasks.

Focuses on factory functions (env-based repo selection) and
build_llm_service logic, using settings manipulation.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from pydantic import SecretStr

from backend.app.settings import Settings

from backend.app.task_support import (
    _build_llm_service,
    _provider_name,
    _use_agents_sdk,
    ai_run_repository,
    blog_repository,
    generation_job_repository,
    idea_repository,
    llm_service_for_idea,
    llm_service_for_news_item,
    news_source_repository,
    news_raw_item_repository,
    submitted_link_repository,
)


# ── Backend detection ──


class TestUseAgentsSdk:
    def test_default_is_false(self) -> None:
        s = Settings()
        assert _use_agents_sdk(s) is False

    def test_agents_sdk_backend(self) -> None:
        s = Settings()
        s.llm_backend = "agents_sdk"
        assert _use_agents_sdk(s) is True

    def test_openai_backend(self) -> None:
        s = Settings()
        s.llm_backend = "openai"
        assert _use_agents_sdk(s) is False


class TestProviderName:
    def test_openai(self) -> None:
        s = Settings()
        assert _provider_name(s) == "openai"

    def test_agents_sdk(self) -> None:
        s = Settings()
        s.llm_backend = "agents_sdk"
        assert _provider_name(s) == "agents_sdk"


# ── Repository factory functions (test environment) ──


class TestRepositoryFactories:
    def test_news_source_repo_in_test_env(self) -> None:
        s = Settings()
        s.environment = "test"
        repo = news_source_repository(s)
        from backend.app.news_sources import NewsSourceRepository
        assert isinstance(repo, NewsSourceRepository)

    def test_news_raw_item_repo_in_test_env(self) -> None:
        s = Settings()
        s.environment = "test"
        repo = news_raw_item_repository(s)
        from backend.app.news_crawl import NewsRawItemRepository
        assert isinstance(repo, NewsRawItemRepository)

    def test_idea_repo_in_test_env(self) -> None:
        s = Settings()
        s.environment = "test"
        repo = idea_repository(s)
        from backend.app.blog_ideas import BlogIdeaRepository
        assert isinstance(repo, BlogIdeaRepository)

    def test_blog_repo_in_test_env(self) -> None:
        s = Settings()
        s.environment = "test"
        repo = blog_repository(s)
        from backend.app.blog import BlogRepository
        assert isinstance(repo, BlogRepository)

    def test_generation_job_repo_in_test_env(self) -> None:
        s = Settings()
        s.environment = "test"
        repo = generation_job_repository(s)
        from backend.app.generation_jobs import GenerationJobRepository
        assert isinstance(repo, GenerationJobRepository)

    def test_submitted_link_repo_in_test_env(self) -> None:
        s = Settings()
        s.environment = "test"
        repo = submitted_link_repository(s)
        from backend.app.news_submitted_links import InMemorySubmittedLinkRepository
        assert isinstance(repo, InMemorySubmittedLinkRepository)

    def test_ai_run_repo_in_test_env(self) -> None:
        s = Settings()
        s.environment = "test"
        repo = ai_run_repository(s)
        from backend.app.ai_runs import AiRunRepository
        assert isinstance(repo, AiRunRepository)


# ── _build_llm_service ──


class TestBuildLlmService:
    def test_openai_service(self) -> None:
        with patch("backend.app.task_support._use_agents_sdk", return_value=False):
            s = Settings()
            service = _build_llm_service("sk-test", "gpt-4o", s)
        from backend.app.llm.service import OpenAILLMService
        assert isinstance(service, OpenAILLMService)

    def test_agents_sdk_service(self) -> None:
        with patch("backend.app.task_support._use_agents_sdk", return_value=True):
            s = Settings()
            service = _build_llm_service("sk-test", "gpt-4o", s)
        # Can't import AgentsSDKLLMService if deps not installed, just check type
        assert "AgentsSDKLLMService" in type(service).__name__


# ── llm_service_for_idea ──


class TestLlmServiceForIdea:
    def test_raises_without_api_key(self) -> None:
        s = Settings()
        s.llm_openai_api_key = SecretStr("")
        with pytest.raises(RuntimeError, match="AI_LAB_LLM_OPENAI_API_KEY is not set"):
            llm_service_for_idea("idea_1", s)

    def test_e2e_fake_mode(self) -> None:
        s = Settings()
        s.llm_e2e_fake = True
        service = llm_service_for_idea("idea_1", s)
        from backend.app.llm.recording import RecordingLLMService
        assert isinstance(service, RecordingLLMService)


# ── llm_service_for_news_item ──


class TestLlmServiceForNewsItem:
    def test_returns_none_without_api_key(self) -> None:
        s = Settings()
        s.llm_openai_api_key = SecretStr("")
        result = llm_service_for_news_item("review_1", s)
        assert result is None

    def test_returns_openai_service(self) -> None:
        with patch("backend.app.task_support._use_agents_sdk", return_value=False):
            s = Settings()
            s.llm_openai_api_key = SecretStr("sk-test-key")
            service = llm_service_for_news_item("review_1", s)
        assert service is not None
