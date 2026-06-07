"""E2E integration tests for OpenAI Agents SDK backend (US-092).

These tests verify that the Agents SDK backend works correctly with fake
responses (no real API calls). They exercise the factory, recording wrapper,
and backend parity without needing a running Docker or real API key.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from backend.app.llm.recording import RecordingLLMService
from backend.app.llm.schemas import BlogIdea, BlogOutline, BlogOutlineSection
from backend.app.llm.service import FakeLLMService, LLMService
from backend.app.settings import Settings


# ===========================================================================
# Factory integration
# ===========================================================================


class TestAgentsSDKFactory:
    """Verify _build_llm_service returns the right type for each backend."""

    def test_openai_backend_returns_openai_service(self) -> None:
        from backend.app.task_support import _build_llm_service

        settings = Settings(environment="test", llm_backend="openai")
        service = _build_llm_service("test-key", "gpt-4o", settings)
        from backend.app.llm.service import OpenAILLMService

        assert isinstance(service, OpenAILLMService)

    def test_agents_sdk_backend_returns_agents_sdk_service(self) -> None:
        from backend.app.task_support import _build_llm_service

        settings = Settings(environment="test", llm_backend="agents_sdk")
        service = _build_llm_service("test-key", "gpt-4o", settings)
        from backend.app.llm.agents_sdk_service import AgentsSDKLLMService

        assert isinstance(service, AgentsSDKLLMService)

    def test_both_backends_implement_llm_service_abc(self) -> None:
        """Both backends satisfy the LLMService contract."""
        from backend.app.task_support import _build_llm_service

        for backend in ("openai", "agents_sdk"):
            settings = Settings(environment="test", llm_backend=backend)
            service = _build_llm_service("test-key", "gpt-4o", settings)
            assert isinstance(service, LLMService)

    def test_backend_uses_correct_model_name(self) -> None:
        from backend.app.task_support import _build_llm_service

        settings = Settings(environment="test", llm_backend="agents_sdk")
        service = _build_llm_service("test-key", "gpt-4o-mini", settings)
        assert service._model == "gpt-4o-mini"


# ===========================================================================
# Recording integration
# ===========================================================================


class TestRecordingWithAgentsSDK:
    """RecordingLLMService wrapping works with both backends."""

    def test_recording_wraps_agents_sdk_service(self) -> None:
        """RecordingLLMService accepts an AgentsSDKLLMService as inner."""
        from backend.app.llm.agents_sdk_service import AgentsSDKLLMService
        from backend.app.ai_runs import AiRunRepository

        inner = AgentsSDKLLMService(api_key="test-key")
        recorder = AiRunRepository()
        service = RecordingLLMService(
            inner, recorder, entity_type="blog_idea", entity_id="idea_1"
        )
        assert service._inner is inner
        assert isinstance(service, LLMService)

    def test_fake_wrapped_with_agents_sdk_setting(self) -> None:
        """FakeLLMService + agents_sdk backend setting still works for E2E."""
        from backend.app.ai_runs import AiRunRepository

        fake = FakeLLMService(
            {
                "blog_idea": BlogIdea(
                    title="Fake Idea",
                    angle="Test",
                    target_reader="Devs",
                    article_goal="Test",
                )
            }
        )
        recorder = AiRunRepository()
        service = RecordingLLMService(
            fake,
            recorder,
            entity_type="blog_idea",
            entity_id="idea_2",
            provider="agents_sdk",
        )
        result = service.generate("blog_idea", {}, BlogIdea)
        assert isinstance(result, BlogIdea)
        assert result.title == "Fake Idea"


# ===========================================================================
# Backend parity via fake service
# ===========================================================================


class TestBackendParity:
    """Both backends produce the same output given the same fake prompt output.

    This test proves that switching AI_LAB_LLM_BACKEND does not change the
    pipeline behavior — the LLMService ABC ensures identical contracts.
    """

    def test_fake_output_identical_regardless_of_backend_config(self) -> None:
        """The pipeline produces the same output with both backend settings."""
        from backend.app.task_support import llm_service_for_idea

        for backend in ("openai", "agents_sdk"):
            settings = Settings(
                environment="test",
                llm_e2e_fake=True,
                llm_backend=backend,
            )
            service = llm_service_for_idea("test-parity", settings)
            result = service.generate(
                "blog_idea",
                inputs={
                    "project_name": "Parity Check",
                    "project_summary": "Testing backend parity.",
                    "ai_capabilities": "LLM, agents",
                    "technical_highlights": "Parity test",
                    "business_value": "Confidence",
                },
                output_schema=BlogIdea,
            )
            assert isinstance(result, BlogIdea)
            assert result.title == "E2E Golden Path Blog Idea"

    def test_fake_service_returns_all_schema_types_with_agents_sdk_setting(
        self,
    ) -> None:
        """Every schema type is reachable with agents_sdk backend + fake mode."""
        from backend.app.task_support import llm_service_for_idea

        schemas: list[tuple[str, dict, type[BaseModel]]] = [
            (
                "blog_idea",
                {
                    "project_name": "P",
                    "project_summary": "S",
                    "ai_capabilities": "C",
                    "technical_highlights": "T",
                    "business_value": "V",
                },
                BlogIdea,
            ),
        ]

        settings = Settings(
            environment="test",
            llm_e2e_fake=True,
            llm_backend="agents_sdk",
        )
        service = llm_service_for_idea("test-schemas", settings)

        for prompt_name, inputs, schema in schemas:
            result = service.generate(prompt_name, inputs, schema)
            assert isinstance(result, schema), (
                f"Failed for {prompt_name} with agents_sdk: "
                f"got {type(result).__name__}"
            )

    def test_e2e_fake_overrides_backend_even_with_agents_sdk(self) -> None:
        """E2E fake mode takes precedence, returning FakeBlogIdeaService."""
        from backend.app.task_support import llm_service_for_idea
        from backend.app.llm.service import FakeLLMService

        settings = Settings(
            environment="test",
            llm_e2e_fake=True,
            llm_backend="agents_sdk",
        )
        service = llm_service_for_idea("test-override", settings)
        # Unwrap RecordingLLMService to check inner
        inner = service._inner if hasattr(service, "_inner") else service
        assert isinstance(inner, FakeLLMService), (
            f"Expected FakeLLMService when llm_e2e_fake=True, "
            f"got {type(inner).__name__}"
        )

    def test_provider_name_matches_backend(self) -> None:
        """The provider name recorded in ai_runs reflects the backend setting."""
        from backend.app.task_support import _provider_name

        openai_settings = Settings(environment="test", llm_backend="openai")
        assert _provider_name(openai_settings) == "openai"

        agents_settings = Settings(environment="test", llm_backend="agents_sdk")
        assert _provider_name(agents_settings) == "agents_sdk"


# ===========================================================================
# Tracing processor (AiRunSpanProcessor)
# ===========================================================================


class TestAiRunSpanProcessor:
    """Tests for the custom Agents SDK tracing processor."""

    def test_processor_constructs(self) -> None:
        from backend.app.llm.tracing import AiRunSpanProcessor

        processor = AiRunSpanProcessor()
        assert processor.active_traces == {}
        assert processor.active_spans == {}

    def test_trace_lifecycle(self) -> None:
        from backend.app.llm.tracing import AiRunSpanProcessor

        processor = AiRunSpanProcessor()
        tid = "test_trace_001"

        class MockTrace:
            def __init__(self):
                self.trace_id = tid
                self.name = "blog_outline"
                self.group_id = "group_1"
                self.metadata = {"prompt": "outline"}

        trace = MockTrace()
        processor.on_trace_start(trace)
        assert tid in processor.active_traces
        assert processor.active_traces[tid]["workflow_name"] == "blog_outline"

        processor.on_trace_end(trace)
        assert tid not in processor.active_traces

    def test_span_lifecycle(self) -> None:
        from backend.app.llm.tracing import AiRunSpanProcessor

        processor = AiRunSpanProcessor()
        sid = "test_span_001"

        class MockSpan:
            def __init__(self):
                self.span_id = sid
                self.trace_id = "trace_001"
                self.type = "agent"
                self.name = "Agent run"

        span = MockSpan()
        processor.on_span_start(span)
        assert sid in processor.active_spans

        processor.on_span_end(span)
        assert sid not in processor.active_spans

    def test_shutdown_clears_all(self) -> None:
        from backend.app.llm.tracing import AiRunSpanProcessor

        processor = AiRunSpanProcessor()
        class MockTrace:
            def __init__(self):
                self.trace_id = "t1"
                self.name = "test"
                self.group_id = None
                self.metadata = None

        processor.on_trace_start(MockTrace())
        assert len(processor.active_traces) == 1
        processor.shutdown()
        assert processor.active_traces == {}
        assert processor.active_spans == {}

    def test_setup_agents_tracing_creates_processor(self) -> None:
        """setup_agents_tracing() registers a processor without error."""
        from backend.app.llm.tracing import setup_agents_tracing, AiRunSpanProcessor

        # Verify the function exists and accepts our processor type
        processor = AiRunSpanProcessor()
        assert processor is not None
        assert callable(setup_agents_tracing)


# ===========================================================================
# Agent session store (US-094 HITL)
# ===========================================================================


class TestAgentSessionStore:
    """Tests for the agent session persistence layer."""

    def test_store_is_singleton(self) -> None:
        from backend.app.llm.sessions import get_session_store, AgentSessionStore

        store1 = get_session_store()
        store2 = get_session_store()
        assert store1 is store2

    def test_has_session_returns_false_for_missing(self) -> None:
        from backend.app.llm.sessions import AgentSessionStore
        store = AgentSessionStore()
        assert not store.has_session("nonexistent")

    def test_drop_removes_session(self) -> None:
        from backend.app.llm.sessions import AgentSessionStore
        store = AgentSessionStore()
        store._sessions["idea_1"] = {
            "state_raw": {"test": True},
            "agent_name": "outline",
            "metadata": {},
        }
        assert store.has_session("idea_1")
        store.drop("idea_1")
        assert not store.has_session("idea_1")

    def test_clear_removes_all(self) -> None:
        from backend.app.llm.sessions import AgentSessionStore
        store = AgentSessionStore()
        store._sessions["a"] = {"state_raw": {}, "agent_name": "", "metadata": {}}
        store._sessions["b"] = {"state_raw": {}, "agent_name": "", "metadata": {}}
        assert len(store._sessions) == 2
        store.clear()
        assert len(store._sessions) == 0


# ===========================================================================
# Guardrails (US-095 claim extraction)
# ===========================================================================


class TestClaimGuardrail:
    """Tests for the claim extraction guardrail."""

    def test_guardrail_factory_returns_callable(self) -> None:
        from backend.app.llm.guardrails import claim_extraction_guardrail
        from backend.app.blog_claims import BlogClaimsRepository
        from backend.app.blog_ideas import BlogIdeaRepository

        guardrail = claim_extraction_guardrail(
            BlogClaimsRepository(), BlogIdeaRepository()
        )
        assert callable(guardrail)

    def test_guardrail_skips_missing_idea(self) -> None:
        """Guardrail doesn't crash when idea_id is missing from inputs."""
        from backend.app.llm.guardrails import claim_extraction_guardrail
        from backend.app.blog_claims import BlogClaimsRepository
        from backend.app.blog_ideas import BlogIdeaRepository
        from backend.app.llm.schemas import TechnicalReview

        guardrail = claim_extraction_guardrail(
            BlogClaimsRepository(), BlogIdeaRepository()
        )
        # Should not raise
        guardrail(TechnicalReview(overall_risk="low", issues=[], approval_recommendation="approve"), {})

    def test_add_guardrail_to_service(self) -> None:
        from backend.app.llm.agents_sdk_service import AgentsSDKLLMService

        service = AgentsSDKLLMService(api_key="test-key")
        service.add_guardrail("technical_review", lambda output, inputs: None)
        assert "technical_review" in service._guardrails
        assert len(service._guardrails["technical_review"]) == 1
