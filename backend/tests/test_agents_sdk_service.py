"""Comprehensive tests for AgentsSDKLLMService.

Mocks ``Runner.run_sync()`` so no real API calls are made.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch, sentinel

import pytest
from pydantic import BaseModel, Field

from backend.app.llm.agents_sdk_service import AgentsSDKLLMService, set_tracing_disabled
from backend.app.llm.prompts import PROMPT_REGISTRY
from backend.app.llm.schemas import BlogIdea, MarketingMetadata, TechnicalReview
from backend.app.llm.service import LLMGenerationError, LLMService


# Ensure tracing stays disabled during tests
set_tracing_disabled(True)


# ===========================================================================
# Helpers
# ===========================================================================


class _DummyOutput(BaseModel):
    """Simple schema used in tests that don't need a real schema."""

    content: str = Field(description="Dummy content")
    score: int = Field(default=0)


def _make_mock_result(
    final_output: BaseModel | None = None,
    *,
    has_usage: bool = True,
    input_tokens: int = 50,
    output_tokens: int = 100,
    state: Any = None,
) -> MagicMock:
    """Build a ``RunResult``-shaped mock returned by ``Runner.run_sync``."""
    result = MagicMock()
    result.final_output = final_output or _DummyOutput(content="ok", score=1)
    if has_usage:
        usage = MagicMock()
        usage.input_tokens = input_tokens
        usage.output_tokens = output_tokens
        result.usage = usage
    else:
        result.usage = None
    result.to_state.return_value = state or MagicMock()
    return result


# ===========================================================================
# Construction
# ===========================================================================


class TestConstruction:
    """Service construction with different parameters."""

    def test_constructor_defaults(self) -> None:
        service = AgentsSDKLLMService(api_key="test-key")
        assert service._api_key == "test-key"
        assert service._model == "gpt-4o"
        assert service._entity_id is None
        assert service._session_store is None
        assert service._recorder is None
        assert service._entity_type == ""
        assert service._provider == "agents_sdk"
        assert service._mcp_servers == []

    def test_constructor_with_all_params(self) -> None:
        session_store = MagicMock()
        recorder = MagicMock()
        mcp_servers = [MagicMock()]

        service = AgentsSDKLLMService(
            api_key="test-key",
            model="gpt-4o-mini",
            session_store=session_store,
            entity_id="idea-123",
            recorder=recorder,
            entity_type="blog_idea",
            provider="agents_sdk",
            mcp_servers=mcp_servers,
        )
        assert service._api_key == "test-key"
        assert service._model == "gpt-4o-mini"
        assert service._session_store is session_store
        assert service._entity_id == "idea-123"
        assert service._recorder is recorder
        assert service._entity_type == "blog_idea"
        assert service._provider == "agents_sdk"
        assert service._mcp_servers is mcp_servers

    def test_constructor_custom_model(self) -> None:
        service = AgentsSDKLLMService(api_key="key", model="o3-mini")
        assert service._model == "o3-mini"

    def test_constructor_empty_api_key(self) -> None:
        """The service does not validate the key until first API call."""
        service = AgentsSDKLLMService(api_key="")
        assert service._api_key == ""


# ===========================================================================
# Guardrail registration
# ===========================================================================


class TestGuardrailRegistration:
    """add_output_guardrail and the deprecated add_guardrail."""

    def test_add_output_guardrail(self) -> None:
        service = AgentsSDKLLMService(api_key="test-key")
        guardrail = MagicMock()
        guardrail._name = "test_guardrail"

        service.add_output_guardrail("technical_review", guardrail)

        assert "technical_review" in service._output_guardrails
        assert service._output_guardrails["technical_review"] == [guardrail]

    def test_add_output_guardrail_multiple(self) -> None:
        service = AgentsSDKLLMService(api_key="test-key")
        g1 = MagicMock()
        g2 = MagicMock()

        service.add_output_guardrail("technical_review", g1)
        service.add_output_guardrail("technical_review", g2)

        assert service._output_guardrails["technical_review"] == [g1, g2]

    def test_add_output_guardrail_different_prompts(self) -> None:
        service = AgentsSDKLLMService(api_key="test-key")
        g1 = MagicMock()
        g2 = MagicMock()

        service.add_output_guardrail("technical_review", g1)
        service.add_output_guardrail("blog_outline", g2)

        assert service._output_guardrails["technical_review"] == [g1]
        assert service._output_guardrails["blog_outline"] == [g2]

    def test_add_guardrail_deprecated_with_output_guardrail(self) -> None:
        """Deprecated add_guardrail wraps the value if it's already an OutputGuardrail."""
        service = AgentsSDKLLMService(api_key="test-key")
        guardrail = MagicMock(spec=["_name"])
        # Simulate an OutputGuardrail by making it an instance
        from agents import OutputGuardrail

        # We can't easily construct one, so we test the isinstance check branch
        # by making a mock that passes isinstance for OutputGuardrail
        guardrail.__class__ = OutputGuardrail

        service.add_guardrail("technical_review", guardrail)
        assert service._output_guardrails["technical_review"] == [guardrail]

    def test_add_guardrail_deprecated_with_callable(self) -> None:
        """Deprecated add_guardrail wraps a callable in OutputGuardrail."""
        from agents.guardrail import OutputGuardrail as OG

        service = AgentsSDKLLMService(api_key="test-key")

        async def my_guardrail(ctx, agent, output):
            return MagicMock()

        service.add_guardrail("technical_review", my_guardrail)

        assert len(service._output_guardrails["technical_review"]) == 1
        wrapped = service._output_guardrails["technical_review"][0]
        assert isinstance(wrapped, OG)


# ===========================================================================
# generate() — base class delegation
# ===========================================================================


class TestGenerate:
    """The ``generate()`` method inherited from ``LLMService``."""

    def test_generate_delegates_to_generate_with_usage(self) -> None:
        """generate() calls generate_with_usage and returns the model."""
        service = AgentsSDKLLMService(api_key="test-key")
        expected = BlogIdea(
            title="Test",
            angle="AI",
            target_reader="Devs",
            article_goal="Inform",
        )

        with patch.object(
            service, "generate_with_usage", return_value=(expected, {"total_tokens": 10})
        ) as mock_gwu:
            result = service.generate("blog_idea", {}, BlogIdea)

        assert result is expected
        mock_gwu.assert_called_once_with("blog_idea", {}, BlogIdea)

    def test_generate_unknown_prompt_key_error(self) -> None:
        service = AgentsSDKLLMService(api_key="test-key")
        with pytest.raises(KeyError, match="Unknown prompt"):
            service.generate("nonexistent", {}, BlogIdea)


# ===========================================================================
# generate_with_usage() — the main generation path
# ===========================================================================


class TestGenerateWithUsage:
    """The ``generate_with_usage()`` method with mocked Runner."""

    # ── Successful generation ──────────────────────────────────────────

    def test_successful_generation_returns_output_and_usage(self) -> None:
        expected = _DummyOutput(content="hello", score=42)
        mock_result = _make_mock_result(expected, input_tokens=50, output_tokens=100)

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ):
            service = AgentsSDKLLMService(api_key="test-key")
            output, usage = service.generate_with_usage(
                "blog_idea",
                {
                    "project_name": "Test",
                    "project_summary": "A test",
                    "ai_capabilities": "LLM",
                    "technical_highlights": "None",
                    "business_value": "Value",
                },
                _DummyOutput,
            )

        assert isinstance(output, _DummyOutput)
        assert output.content == "hello"
        assert output.score == 42
        assert usage is not None
        assert usage["prompt_tokens"] == 50
        assert usage["completion_tokens"] == 100
        assert usage["total_tokens"] == 150
        assert "trace_id" in usage

    def test_successful_generation_with_blog_idea_schema(self) -> None:
        """Test with a real schema (BlogIdea) to verify shape."""
        expected = BlogIdea(
            title="AI Evaluation Pipelines",
            angle="Engineering",
            target_reader="CTOs",
            article_goal="Show our workflow",
            positioning_notes=["Avoid hype"],
        )
        mock_result = _make_mock_result(expected)

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ):
            service = AgentsSDKLLMService(api_key="test-key")
            output, usage = service.generate_with_usage(
                "blog_idea",
                {
                    "project_name": "AI Lab",
                    "project_summary": "Test",
                    "ai_capabilities": "LLM",
                    "technical_highlights": "None",
                    "business_value": "Value",
                },
                BlogIdea,
            )

        assert isinstance(output, BlogIdea)
        assert output.title == "AI Evaluation Pipelines"
        assert output.positioning_notes == ["Avoid hype"]

    # ── Error handling ─────────────────────────────────────────────────

    def test_unknown_prompt_raises_key_error(self) -> None:
        service = AgentsSDKLLMService(api_key="test-key")
        with pytest.raises(KeyError, match="Unknown prompt"):
            service.generate_with_usage("nonexistent_prompt", {}, _DummyOutput)

    def test_runner_failure_raises_llm_generation_error(self) -> None:
        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            side_effect=RuntimeError("API timeout"),
        ):
            service = AgentsSDKLLMService(api_key="test-key")
            with pytest.raises(
                LLMGenerationError, match="Agents SDK call failed for prompt 'blog_idea'"
            ):
                service.generate_with_usage(
                    "blog_idea",
                    {
                        "project_name": "Test",
                        "project_summary": "Test",
                        "ai_capabilities": "LLM",
                        "technical_highlights": "None",
                        "business_value": "Value",
                    },
                    _DummyOutput,
                )

    def test_wrong_output_type_raises_llm_generation_error(self) -> None:
        """When final_output is not an instance of output_schema."""
        mock_result = _make_mock_result()
        mock_result.final_output = "not a pydantic model"

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ):
            service = AgentsSDKLLMService(api_key="test-key")
            with pytest.raises(
                LLMGenerationError, match="Agents SDK returned unexpected type"
            ):
                service.generate_with_usage(
                    "blog_idea",
                    {
                        "project_name": "Test",
                        "project_summary": "Test",
                        "ai_capabilities": "LLM",
                        "technical_highlights": "None",
                        "business_value": "Value",
                    },
                    _DummyOutput,
                )

    # ── Usage edge cases ───────────────────────────────────────────────

    def test_no_usage_when_result_usage_is_none(self) -> None:
        mock_result = _make_mock_result(has_usage=False)

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ):
            service = AgentsSDKLLMService(api_key="test-key")
            output, usage = service.generate_with_usage(
                "blog_idea",
                {
                    "project_name": "Test",
                    "project_summary": "Test",
                    "ai_capabilities": "LLM",
                    "technical_highlights": "None",
                    "business_value": "Value",
                },
                _DummyOutput,
            )

        assert usage is not None
        # Only trace_id should be set when result.usage is None
        assert "prompt_tokens" not in usage
        assert "trace_id" in usage

    # ── Session store ──────────────────────────────────────────────────

    def test_session_store_save_on_success(self) -> None:
        session_store = MagicMock()
        mock_state = MagicMock()
        mock_result = _make_mock_result(state=mock_state)

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ):
            service = AgentsSDKLLMService(
                api_key="test-key",
                session_store=session_store,
                entity_id="idea-1",
            )
            service.generate_with_usage(
                "blog_idea",
                {
                    "project_name": "Test",
                    "project_summary": "Test",
                    "ai_capabilities": "LLM",
                    "technical_highlights": "None",
                    "business_value": "Value",
                },
                _DummyOutput,
            )

        mock_result.to_state.assert_called_once()
        session_store.save.assert_called_once_with(
            "idea-1",
            mock_state,
            agent_name="blog_idea",
            metadata={"prompt_name": "blog_idea", "model": "gpt-4o"},
        )

    def test_session_store_not_called_without_entity_id(self) -> None:
        session_store = MagicMock()
        mock_result = _make_mock_result()

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ):
            service = AgentsSDKLLMService(
                api_key="test-key", session_store=session_store
            )
            service.generate_with_usage(
                "blog_idea",
                {
                    "project_name": "Test",
                    "project_summary": "Test",
                    "ai_capabilities": "LLM",
                    "technical_highlights": "None",
                    "business_value": "Value",
                },
                _DummyOutput,
            )

        session_store.save.assert_not_called()

    def test_session_store_not_called_without_session_store(self) -> None:
        mock_result = _make_mock_result()

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ):
            service = AgentsSDKLLMService(
                api_key="test-key", entity_id="idea-1"
            )
            service.generate_with_usage(
                "blog_idea",
                {
                    "project_name": "Test",
                    "project_summary": "Test",
                    "ai_capabilities": "LLM",
                    "technical_highlights": "None",
                    "business_value": "Value",
                },
                _DummyOutput,
            )

        # No session_store, so no call; should not raise

    def test_session_store_save_exception_is_silently_caught(self) -> None:
        """An exception in session_store.save should not propagate."""
        session_store = MagicMock()
        session_store.save.side_effect = RuntimeError("DB unavailable")
        mock_result = _make_mock_result()

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ):
            service = AgentsSDKLLMService(
                api_key="test-key",
                session_store=session_store,
                entity_id="idea-1",
            )
            # Should not raise despite the session store error
            output, usage = service.generate_with_usage(
                "blog_idea",
                {
                    "project_name": "Test",
                    "project_summary": "Test",
                    "ai_capabilities": "LLM",
                    "technical_highlights": "None",
                    "business_value": "Value",
                },
                _DummyOutput,
            )

        assert output is not None
        session_store.save.assert_called_once()

    # ── Recorder on success ────────────────────────────────────────────

    def test_recorder_record_completed_on_success(self) -> None:
        recorder = MagicMock()
        expected = _DummyOutput(content="success", score=99)
        mock_result = _make_mock_result(expected, input_tokens=10, output_tokens=20)

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ), patch(
            "agents.gen_trace_id",
            return_value="trace-abc",
        ):
            service = AgentsSDKLLMService(
                api_key="test-key",
                entity_id="idea-1",
                recorder=recorder,
                entity_type="blog_idea",
            )
            service.generate_with_usage(
                "blog_idea",
                {
                    "project_name": "Test",
                    "project_summary": "Test",
                    "ai_capabilities": "LLM",
                    "technical_highlights": "None",
                    "business_value": "Value",
                },
                _DummyOutput,
            )

        recorder.record_completed.assert_called_once_with(
            prompt_name="blog_idea",
            entity_type="blog_idea",
            entity_id="idea-1",
            provider="agents_sdk",
            model="gpt-4o",
            input_payload={
                "project_name": "Test",
                "project_summary": "Test",
                "ai_capabilities": "LLM",
                "technical_highlights": "None",
                "business_value": "Value",
            },
            output_payload=expected.model_dump(),
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            latency_ms=recorder.record_completed.call_args[1]["latency_ms"],
            trace_id="trace-abc",
        )

    def test_recorder_not_called_without_entity_id(self) -> None:
        recorder = MagicMock()
        mock_result = _make_mock_result()

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ):
            service = AgentsSDKLLMService(
                api_key="test-key", recorder=recorder
            )
            service.generate_with_usage(
                "blog_idea",
                {
                    "project_name": "Test",
                    "project_summary": "Test",
                    "ai_capabilities": "LLM",
                    "technical_highlights": "None",
                    "business_value": "Value",
                },
                _DummyOutput,
            )

        recorder.record_completed.assert_not_called()

    def test_recorder_not_called_without_recorder(self) -> None:
        mock_result = _make_mock_result()

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ):
            service = AgentsSDKLLMService(
                api_key="test-key", entity_id="idea-1"
            )
            service.generate_with_usage(
                "blog_idea",
                {
                    "project_name": "Test",
                    "project_summary": "Test",
                    "ai_capabilities": "LLM",
                    "technical_highlights": "None",
                    "business_value": "Value",
                },
                _DummyOutput,
            )

        # No recorder, no error

    # ── Recorder on failure ────────────────────────────────────────────

    def test_recorder_record_failed_on_runner_exception(self) -> None:
        recorder = MagicMock()

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            side_effect=ValueError("invalid request"),
        ):
            service = AgentsSDKLLMService(
                api_key="test-key",
                entity_id="idea-1",
                recorder=recorder,
                entity_type="blog_idea",
            )
            with pytest.raises(LLMGenerationError):
                service.generate_with_usage(
                    "blog_idea",
                    {
                        "project_name": "Test",
                        "project_summary": "Test",
                        "ai_capabilities": "LLM",
                        "technical_highlights": "None",
                        "business_value": "Value",
                    },
                    _DummyOutput,
                )

        recorder.record_failed.assert_called_once_with(
            prompt_name="blog_idea",
            entity_type="blog_idea",
            entity_id="idea-1",
            provider="agents_sdk",
            model="gpt-4o",
            input_payload={
                "project_name": "Test",
                "project_summary": "Test",
                "ai_capabilities": "LLM",
                "technical_highlights": "None",
                "business_value": "Value",
            },
            error_message="invalid request",
            latency_ms=recorder.record_failed.call_args[1]["latency_ms"],
        )

    def test_recorder_record_failed_not_called_without_entity_id(self) -> None:
        recorder = MagicMock()

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            side_effect=ValueError("fail"),
        ):
            service = AgentsSDKLLMService(
                api_key="test-key", recorder=recorder
            )
            with pytest.raises(LLMGenerationError):
                service.generate_with_usage(
                    "blog_idea",
                    {
                        "project_name": "Test",
                        "project_summary": "Test",
                        "ai_capabilities": "LLM",
                        "technical_highlights": "None",
                        "business_value": "Value",
                    },
                    _DummyOutput,
                )

        recorder.record_failed.assert_not_called()

    # ── Max tokens for draft prompts ───────────────────────────────────

    def test_draft_writer_passes_max_tokens(self) -> None:
        mock_result = _make_mock_result()

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ) as mock_run:
            service = AgentsSDKLLMService(api_key="test-key")
            service.generate_with_usage(
                "draft_writer",
                {
                    "outline_json": "{}",
                    "project_context": "test",
                    "positioning_notes": "",
                },
                _DummyOutput,
            )

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("max_tokens") == 16000

    def test_draft_section_writer_passes_max_tokens(self) -> None:
        mock_result = _make_mock_result()

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ) as mock_run:
            service = AgentsSDKLLMService(api_key="test-key")
            service.generate_with_usage(
                "draft_section_writer",
                {
                    "outline_json": "{}",
                    "project_context": "test",
                    "positioning_notes": "",
                    "section_index": "1",
                    "section_total": "5",
                    "section_heading": "Intro",
                    "section_points": "point",
                    "prior_sections_summary": "none",
                },
                _DummyOutput,
            )

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("max_tokens") == 16000

    def test_non_draft_prompt_does_not_pass_max_tokens(self) -> None:
        mock_result = _make_mock_result()

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ) as mock_run:
            service = AgentsSDKLLMService(api_key="test-key")
            service.generate_with_usage(
                "blog_outline",
                {
                    "title": "Test",
                    "angle": "AI",
                    "target_reader": "Devs",
                    "article_goal": "Inform",
                    "positioning_notes": "",
                    "project_context": "test",
                },
                _DummyOutput,
            )

        call_kwargs = mock_run.call_args[1]
        assert "max_tokens" not in call_kwargs

    # ── Runner.run_sync arguments ──────────────────────────────────────

    def test_runner_called_with_correct_agent_and_input(self) -> None:
        expected = BlogIdea(
            title="Test",
            angle="AI",
            target_reader="Devs",
            article_goal="Inform",
        )
        mock_result = _make_mock_result(expected)

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ) as mock_run:
            service = AgentsSDKLLMService(api_key="test-key", model="gpt-4o-mini")
            service.generate_with_usage(
                "blog_idea",
                {
                    "project_name": "My Project",
                    "project_summary": "Summary text",
                    "ai_capabilities": "LLM",
                    "technical_highlights": "None",
                    "business_value": "Value",
                },
                BlogIdea,
            )

        call_args, call_kwargs = mock_run.call_args
        agent = call_args[0]
        user_input = call_args[1]

        assert agent.name == "blog_idea"
        assert agent.model == "gpt-4o-mini"
        assert agent.output_type is BlogIdea
        assert "My Project" in user_input
        assert "Summary text" in user_input
        assert "hooks" in call_kwargs
        assert "run_config" in call_kwargs

    def test_runner_receives_output_guardrails(self) -> None:
        expected = BlogIdea(
            title="Test",
            angle="AI",
            target_reader="Devs",
            article_goal="Inform",
        )
        mock_result = _make_mock_result(expected)
        guardrail = MagicMock(spec=["_name"])

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ) as mock_run:
            service = AgentsSDKLLMService(api_key="test-key")
            service.add_output_guardrail("blog_idea", guardrail)
            service.generate_with_usage(
                "blog_idea",
                {
                    "project_name": "Test",
                    "project_summary": "Test",
                    "ai_capabilities": "LLM",
                    "technical_highlights": "None",
                    "business_value": "Value",
                },
                BlogIdea,
            )

        call_args = mock_run.call_args[0]
        agent = call_args[0]
        assert agent.output_guardrails == [guardrail]


# ===========================================================================
# MCP servers
# ===========================================================================


class TestMCPServers:
    """MCP server passthrough to Agent."""

    def test_mcp_servers_passed_to_agent(self) -> None:
        mcp_server = MagicMock()
        expected = BlogIdea(
            title="Test",
            angle="AI",
            target_reader="Devs",
            article_goal="Inform",
        )
        mock_result = _make_mock_result(expected)

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ) as mock_run:
            service = AgentsSDKLLMService(
                api_key="test-key",
                mcp_servers=[mcp_server],
            )
            service.generate_with_usage(
                "blog_idea",
                {
                    "project_name": "Test",
                    "project_summary": "Test",
                    "ai_capabilities": "LLM",
                    "technical_highlights": "None",
                    "business_value": "Value",
                },
                BlogIdea,
            )

        agent = mock_run.call_args[0][0]
        assert agent.mcp_servers == [mcp_server]


# ===========================================================================
# Edge cases / integration
# ===========================================================================


class TestEdgeCases:
    """Edge cases for recording, sessions, and error scenarios."""

    def test_generate_with_technical_review_schema(self) -> None:
        """Verify with a more complex nested schema."""
        expected = TechnicalReview(
            overall_risk="low",
            issues=[],
            approval_recommendation="approve",
        )
        mock_result = _make_mock_result(expected)

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ):
            service = AgentsSDKLLMService(api_key="test-key")
            output, usage = service.generate_with_usage(
                "technical_review",
                {"draft_markdown": "# Draft", "project_context": "test"},
                TechnicalReview,
            )

        assert isinstance(output, TechnicalReview)
        assert output.overall_risk == "low"

    def test_provider_default_value(self) -> None:
        service = AgentsSDKLLMService(api_key="test-key")
        assert service._provider == "agents_sdk"

    def test_entity_type_defaults_to_empty_string(self) -> None:
        service = AgentsSDKLLMService(api_key="test-key")
        assert service._entity_type == ""

    def test_trace_id_in_usage(self) -> None:
        """Verify the trace_id from run_config appears in the usage dict."""
        mock_result = _make_mock_result()

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ), patch(
            "agents.gen_trace_id",
            return_value="custom-trace-id",
        ):
            service = AgentsSDKLLMService(api_key="test-key")
            _, usage = service.generate_with_usage(
                "blog_idea",
                {
                    "project_name": "Test",
                    "project_summary": "Test",
                    "ai_capabilities": "LLM",
                    "technical_highlights": "None",
                    "business_value": "Value",
                },
                _DummyOutput,
            )

        assert usage["trace_id"] == "custom-trace-id"

    def test_output_guardrails_empty_when_none_registered(self) -> None:
        """When no guardrails are registered, agent gets None, not empty list."""
        mock_result = _make_mock_result()

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ) as mock_run:
            service = AgentsSDKLLMService(api_key="test-key")
            service.generate_with_usage(
                "blog_idea",
                {
                    "project_name": "Test",
                    "project_summary": "Test",
                    "ai_capabilities": "LLM",
                    "technical_highlights": "None",
                    "business_value": "Value",
                },
                _DummyOutput,
            )

        agent = mock_run.call_args[0][0]
        assert agent.output_guardrails == []


# ===========================================================================
# Factory function
# ===========================================================================


class TestLLMBackendSelection:
    """Test that the factory selects the right backend."""

    def test_agents_sdk_has_correct_provider(self) -> None:
        """When _use_agents_sdk is True, the service gets provider='agents_sdk'."""
        from backend.app.llm.agents_sdk_service import AgentsSDKLLMService

        service = AgentsSDKLLMService(api_key="key", provider="agents_sdk")
        assert service._provider == "agents_sdk"

    def test_backend_selection_via_settings(self) -> None:
        """Verify _use_agents_sdk returns True when llm_backend=agents_sdk."""
        from backend.app.settings import Settings
        from backend.app.task_support import _use_agents_sdk

        settings = Settings(llm_backend="agents_sdk")
        assert _use_agents_sdk(settings)

        settings = Settings(llm_backend="openai")
        assert not _use_agents_sdk(settings)

    def test_build_llm_service_returns_agents_sdk(self) -> None:
        """Integration: _build_llm_service with agents_sdk returns AgentsSDKLLMService."""
        from unittest.mock import patch as _patch

        with _patch("backend.app.task_support.Settings") as MockSettings:
            mock_settings = MagicMock()
            mock_settings.llm_backend = "agents_sdk"
            mock_settings.llm_mcp_enabled = False
            MockSettings.return_value = mock_settings

            from backend.app.task_support import _build_llm_service

            service = _build_llm_service(
                api_key="key", model="gpt-4o", settings=mock_settings
            )
            assert isinstance(service, AgentsSDKLLMService)
            assert service._model == "gpt-4o"

    def test_llm_service_for_idea_with_agents_sdk(self) -> None:
        """Verify llm_service_for_idea returns AgentsSDKLLMService when configured."""
        from unittest.mock import patch as _patch

        with _patch("backend.app.task_support.Settings") as MockSettings:
            mock_settings = MagicMock()
            mock_settings.llm_backend = "agents_sdk"
            mock_settings.llm_mcp_enabled = False
            mock_settings.llm_e2e_fake = False
            mock_settings.llm_openai_api_key = MagicMock()
            mock_settings.llm_openai_api_key.get_secret_value.return_value = "test-key"
            mock_settings.llm_model = "gpt-4o"
            mock_settings.environment = "test"
            MockSettings.return_value = mock_settings

            # We need to patch ai_run_repository too to avoid DB init
            with _patch("backend.app.task_support.ai_run_repository", return_value=None):
                from backend.app.task_support import llm_service_for_idea

                service = llm_service_for_idea("idea-123", mock_settings)
                assert isinstance(service, AgentsSDKLLMService)
