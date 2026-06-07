"""Tests for the LLM service, schemas, and prompt registry.

The LLM service tests use ``FakeLLMService`` so they never call a real API.
Schema tests verify Pydantic validation rules.
Prompt registry tests verify template rendering.
"""

import json
import sys

import pytest
from pydantic import ValidationError

from backend.app.llm.prompts import PROMPT_REGISTRY, BLOG_IDEA_PROMPT, PromptTemplate
from backend.app.llm.schemas import (
    BlogIdea,
    BlogOutline,
    BlogOutlineSection,
    BlogDraft,
    TechnicalReview,
    TechnicalReviewIssue,
    MarketingMetadata,
    NewsScoring,
)
from backend.app.llm.service import (
    FakeLLMService,
    LLMGenerationError,
    LLMService,
)


# The Agents SDK service requires an API key, so we use fixture-level
# monkeypatching to test structural aspects without real HTTP calls.


# ===========================================================================
# Prompt registry
# ===========================================================================


class TestPromptRegistry:
    def test_all_prompts_are_registered(self) -> None:
        """Every prompt name used by the blog workflow is present."""
        expected = {
            "blog_idea",
            "blog_outline",
            "draft_writer",
            "technical_review",
            "marketing_metadata",
            "claim_extraction",
            "ai_news_scoring",
        }
        assert expected.issubset(PROMPT_REGISTRY.keys())

    def test_prompt_template_is_pydantic_model(self) -> None:
        assert isinstance(BLOG_IDEA_PROMPT, PromptTemplate)
        assert len(BLOG_IDEA_PROMPT.system) > 0
        assert len(BLOG_IDEA_PROMPT.user_template) > 0

    def test_user_template_has_placeholder(self) -> None:
        assert "{project_name}" in BLOG_IDEA_PROMPT.user_template
        assert "{project_summary}" in BLOG_IDEA_PROMPT.user_template

    def test_user_template_renders_with_inputs(self) -> None:
        rendered = BLOG_IDEA_PROMPT.user_template.format(
            project_name="Test Project",
            project_summary="A test project for validation.",
            ai_capabilities="LLM, evaluation",
            technical_highlights="Structured output",
            business_value="Reduce manual work",
        )
        assert "Test Project" in rendered
        assert "A test project for validation." in rendered


# ===========================================================================
# Schemas
# ===========================================================================


class TestBlogIdeaSchema:
    def test_valid_blog_idea(self) -> None:
        idea = BlogIdea(
            title="How We Built an AI Evaluation Pipeline",
            angle="AI Evaluation",
            target_reader="CTO evaluating AI adoption",
            article_goal="Show our evaluation process",
            positioning_notes=["Avoid overpromising autonomy"],
        )
        assert idea.title == "How We Built an AI Evaluation Pipeline"
        assert "Avoid overpromising autonomy" in idea.positioning_notes

    def test_minimal_blog_idea(self) -> None:
        """positioning_notes defaults to empty list."""
        idea = BlogIdea(
            title="Minimal idea",
            angle="Test",
            target_reader="Developers",
            article_goal="Test goal",
        )
        assert idea.positioning_notes == []


class TestBlogOutlineSchema:
    def test_valid_outline(self) -> None:
        outline = BlogOutline(
            title="Test Article",
            outline=[
                BlogOutlineSection(
                    section="Context",
                    points=["Project background", "Team size"],
                ),
                BlogOutlineSection(
                    section="Problem",
                    points=["What we were solving"],
                ),
            ],
        )
        assert len(outline.outline) == 2
        assert outline.outline[0].points == ["Project background", "Team size"]


class TestBlogDraftSchema:
    def test_valid_draft(self) -> None:
        draft = BlogDraft(
            title="Test Draft",
            markdown="# Hello\n\nThis is a test draft.",
        )
        assert "# Hello" in draft.markdown


class TestTechnicalReviewSchema:
    def test_valid_review_no_issues(self) -> None:
        review = TechnicalReview(
            overall_risk="low",
            issues=[],
            approval_recommendation="approve",
        )
        assert review.overall_risk == "low"

    def test_valid_review_with_issues(self) -> None:
        review = TechnicalReview(
            overall_risk="medium",
            issues=[
                TechnicalReviewIssue(
                    severity="high",
                    type="unsupported_claim",
                    text="Our AI reduces cost by 80%",
                    reason="No measurement data provided",
                    suggestion='Use "noticeable reduction" instead',
                ),
            ],
            approval_recommendation="needs_revision",
        )
        assert len(review.issues) == 1
        assert review.issues[0].severity == "high"

    @pytest.mark.parametrize(
        "field,value",
        [
            ("overall_risk", "critical"),
            ("approval_recommendation", "maybe"),
        ],
    )
    def test_invalid_enum_values_are_rejected(self, field: str, value: str) -> None:
        data = {
            "overall_risk": "low",
            "issues": [],
            "approval_recommendation": "approve",
        }
        data[field] = value
        with pytest.raises(ValidationError):
            TechnicalReview(**data)

    def test_invalid_severity_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TechnicalReview(
                overall_risk="low",
                issues=[
                    TechnicalReviewIssue(
                        severity="urgent",
                        type="unsupported_claim",
                        text="Test",
                        reason="Test",
                        suggestion="Test",
                    ),
                ],
                approval_recommendation="approve",
            )


class TestNewsScoringSchema:
    def test_valid_news_scoring(self) -> None:
        scoring = NewsScoring(
            source_credibility_score=0.8,
            engagement_score=0.5,
            relevance_score=0.9,
            novelty_score=0.7,
            technical_depth_score=0.6,
            business_value_score=0.6,
            spam_risk_score=0.1,
            final_publish_score=0.78,
            summary="OpenAI released a model update.",
            why_it_matters="Practitioners should evaluate the API impact.",
        )
        assert scoring.final_publish_score == 0.78

    def test_invalid_news_scoring_score_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NewsScoring(
                source_credibility_score=1.2,
                engagement_score=0.5,
                relevance_score=0.9,
                novelty_score=0.7,
                technical_depth_score=0.6,
                business_value_score=0.6,
                spam_risk_score=0.1,
                final_publish_score=0.78,
                summary="Summary",
                why_it_matters="Why",
            )


class TestMarketingMetadataSchema:
    def test_valid_metadata(self) -> None:
        meta = MarketingMetadata(
            seo_title="AI Evaluation at AI Lab",
            meta_description="Learn how we built an evaluation pipeline.",
            excerpt="A practical evaluation case study.",
            linkedin_post="We built an AI evaluation pipeline. Here's what we learned.",
            x_post="We built an AI evaluation pipeline. Here's what we learned.",
            cta="Contact our AI/LLM Lab to learn more.",
        )
        assert len(meta.seo_title) <= 60
        assert len(meta.meta_description) <= 160


# ===========================================================================
# LLM Service
# ===========================================================================


class TestLLMService:
    def test_fake_service_returns_canned_response(self) -> None:
        expected = BlogIdea(
            title="Test Idea",
            angle="AI Evaluation",
            target_reader="CTOs",
            article_goal="Show evaluation",
        )
        service: LLMService = FakeLLMService(responses={"blog_idea": expected})

        result = service.generate("blog_idea", {}, BlogIdea)
        assert isinstance(result, BlogIdea)
        assert result.title == "Test Idea"

    def test_fake_service_raises_on_missing_prompt(self) -> None:
        service: LLMService = FakeLLMService(responses={})

        with pytest.raises(LLMGenerationError, match="No fake response configured"):
            service.generate("blog_idea", {}, BlogIdea)

    def test_fake_service_serializes_like_real_output(self) -> None:
        """Ensure the fake output can be JSON-serialized (like a real API response)."""
        expected = BlogIdea(
            title="Serializable Idea",
            angle="AI Evaluation",
            target_reader="Developers",
            article_goal="Test serialization",
        )
        service: LLMService = FakeLLMService(responses={"blog_idea": expected})

        result = service.generate("blog_idea", {}, BlogIdea)
        raw = result.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["title"] == "Serializable Idea"

    def test_fake_service_with_all_schema_types(self) -> None:
        """Verify the fake can return every schema type."""
        schemas: dict[str, tuple[dict, type]] = {
            "blog_idea": (
                {
                    "title": "Idea",
                    "angle": "Tech",
                    "target_reader": "Devs",
                    "article_goal": "Inform",
                },
                BlogIdea,
            ),
            "blog_outline": (
                {
                    "title": "Outline",
                    "outline": [
                        {
                            "section": "Context",
                            "points": ["Background"],
                        },
                    ],
                },
                BlogOutline,
            ),
            "draft": (
                {
                    "title": "Draft",
                    "markdown": "# Content",
                },
                BlogDraft,
            ),
            "review": (
                {
                    "overall_risk": "low",
                    "issues": [],
                    "approval_recommendation": "approve",
                },
                TechnicalReview,
            ),
            "marketing": (
                {
                    "seo_title": "SEO",
                    "meta_description": "Desc",
                    "excerpt": "Excerpt",
                    "linkedin_post": "LinkedIn",
                    "x_post": "X/Twitter",
                    "cta": "CTA",
                },
                MarketingMetadata,
            ),
        }

        for name, (data, schema) in schemas.items():
            obj = schema(**data)
            service: LLMService = FakeLLMService(responses={name: obj})
            result = service.generate(name, {}, schema)
            assert isinstance(result, schema), f"Failed for {name}"


# ===========================================================================
# Prompt + service integration (via fake)
# ===========================================================================


class TestPromptServiceIntegration:
    def test_prompt_registry_entries_match_service_expected_names(self) -> None:
        """All registered prompts should be usable by the service."""
        idea = BlogIdea(
            title="Integration Idea",
            angle="Test",
            target_reader="Devs",
            article_goal="Integrate",
        )
        service: LLMService = FakeLLMService(responses={"blog_idea": idea})

        for name in PROMPT_REGISTRY:
            # FakeLLMService will raise if it has no response for this name
            try:
                service.generate(name, {}, BlogIdea)
            except LLMGenerationError:
                pass  # Expected for names not in responses dict


# ===========================================================================
# Agents SDK Service (structural tests — no real API calls)
# ===========================================================================


class TestAgentsSDKLLMService:
    """Test the Agents SDK LLM service without calling real APIs.

    The Agents SDK tries to make network calls on ``Runner.run_sync()``, so
    these tests focus on construction, prompt lookup, and error handling.
    Full pipeline verification is covered by E2E tests with fake backend.
    """

    def test_constructor(self) -> None:
        from backend.app.llm.agents_sdk_service import AgentsSDKLLMService

        service = AgentsSDKLLMService(api_key="test-key", model="gpt-4o")
        assert service._api_key == "test-key"
        assert service._model == "gpt-4o"

    def test_unknown_prompt_raises_key_error(self) -> None:
        from backend.app.llm.agents_sdk_service import AgentsSDKLLMService

        service = AgentsSDKLLMService(api_key="test-key")
        with pytest.raises(KeyError, match="Unknown prompt"):
            service.generate("nonexistent_prompt", {}, BlogIdea)

    def test_missing_api_key_still_constructs(self) -> None:
        """The service does not validate the key until first API call."""
        from backend.app.llm.agents_sdk_service import AgentsSDKLLMService

        service = AgentsSDKLLMService(api_key="")
        assert service._api_key == ""

    def test_all_prompts_have_system_and_user_template(self) -> None:
        """Verify every registered prompt has non-empty system + user_template."""
        for name in PROMPT_REGISTRY:
            prompt = PROMPT_REGISTRY[name]
            assert len(prompt.system) > 0, f"Prompt '{name}' has empty system"
            assert len(prompt.user_template) > 0, f"Prompt '{name}' has empty user_template"


# ===========================================================================
# Backend selection (task_support factory)
# ===========================================================================


class TestLLMBackendSelection:
    """Test that the factory function selects the right backend."""

    def test_default_is_openai(self) -> None:
        from backend.app.settings import Settings
        from backend.app.task_support import _use_agents_sdk

        settings = Settings(llm_backend="openai")
        assert not _use_agents_sdk(settings)

    def test_agents_sdk_selected_when_configured(self) -> None:
        from backend.app.settings import Settings
        from backend.app.task_support import _use_agents_sdk

        settings = Settings(llm_backend="agents_sdk")
        assert _use_agents_sdk(settings)

    def test_fake_overrides_backend(self) -> None:
        """E2E fake mode takes precedence over backend selection."""
        from backend.app.settings import Settings
        from backend.app.task_support import llm_service_for_idea

        # E2E fake + agents_sdk backend — should still return fake service
        settings = Settings(
            llm_e2e_fake=True,
            llm_backend="agents_sdk",
        )
        service = llm_service_for_idea("test-idea-id", settings)
        from backend.app.llm.service import FakeLLMService

        # The inner service (unwrapped from RecordingLLMService)
        inner = service._inner if hasattr(service, "_inner") else service
        assert isinstance(inner, FakeLLMService), (
            f"Expected FakeLLMService, got {type(inner).__name__}"
        )


# ===========================================================================
# RecordingLLMService
# ===========================================================================


class TestRecordingLLMService:
    """Test the RecordingLLMService wrapper that persists AI run metadata."""

    def make_blog_idea(self) -> BlogIdea:
        return BlogIdea(
            title="Recording Test",
            angle="AI Evaluation",
            target_reader="CTOs",
            article_goal="Test recording",
        )

    def test_delegates_to_inner_service(self) -> None:
        """RecordingLLMService returns the inner service result."""
        from backend.app.ai_runs import AiRunRepository
        from backend.app.llm.recording import RecordingLLMService

        expected = self.make_blog_idea()
        inner = FakeLLMService(responses={"blog_idea": expected})
        recorder = AiRunRepository()
        service = RecordingLLMService(
            inner=inner,
            recorder=recorder,
            entity_type="blog_idea",
            entity_id="idea_123",
        )

        result = service.generate("blog_idea", {}, BlogIdea)
        assert result.title == "Recording Test"

    def test_records_completed_run(self) -> None:
        """Successful generation records a completed AiRun."""
        from backend.app.ai_runs import AiRunRepository
        from backend.app.llm.recording import RecordingLLMService

        expected = self.make_blog_idea()
        inner = FakeLLMService(responses={"blog_idea": expected})
        recorder = AiRunRepository()
        service = RecordingLLMService(
            inner=inner,
            recorder=recorder,
            entity_type="blog_idea",
            entity_id="idea_001",
        )

        service.generate("blog_idea", {}, BlogIdea)

        runs = recorder.list_for_entity("blog_idea", "idea_001")
        assert len(runs) == 1
        assert runs[0].status == "completed"
        assert runs[0].prompt_name == "blog_idea"
        assert runs[0].output_payload["title"] == "Recording Test"

    def test_records_failed_on_llm_generation_error(self) -> None:
        """Failure from inner service records a failed AiRun and re-raises."""
        from unittest.mock import MagicMock

        from backend.app.ai_runs import AiRunRepository
        from backend.app.llm.recording import RecordingLLMService

        inner = MagicMock(spec=FakeLLMService)
        inner.generate_with_usage.side_effect = LLMGenerationError("API failure")
        recorder = AiRunRepository()
        service = RecordingLLMService(
            inner=inner,
            recorder=recorder,
            entity_type="blog_idea",
            entity_id="idea_002",
        )

        with pytest.raises(LLMGenerationError, match="API failure"):
            service.generate("blog_idea", {}, BlogIdea)

        runs = recorder.list_for_entity("blog_idea", "idea_002")
        assert len(runs) == 1
        assert runs[0].status == "failed"
        assert "API failure" in runs[0].error_message

    def test_records_failed_on_generic_exception(self) -> None:
        """Non-LLMGenerationError exceptions are wrapped and recorded."""
        from unittest.mock import MagicMock

        from backend.app.ai_runs import AiRunRepository
        from backend.app.llm.recording import RecordingLLMService

        inner = MagicMock(spec=FakeLLMService)
        inner.generate_with_usage.side_effect = ValueError("unexpected error")
        recorder = AiRunRepository()
        service = RecordingLLMService(
            inner=inner,
            recorder=recorder,
            entity_type="blog_idea",
            entity_id="idea_003",
        )

        with pytest.raises(LLMGenerationError, match="unexpected error"):
            service.generate("blog_idea", {}, BlogIdea)

        runs = recorder.list_for_entity("blog_idea", "idea_003")
        assert len(runs) == 1
        assert runs[0].status == "failed"
        assert "unexpected error" in runs[0].error_message

    def test_records_usage_tokens(self) -> None:
        """Token usage from inner service is passed to the recorder."""
        from backend.app.ai_runs import AiRunRepository
        from backend.app.llm.recording import RecordingLLMService

        expected = self.make_blog_idea()
        inner = FakeLLMService(responses={"blog_idea": expected})
        recorder = AiRunRepository()
        service = RecordingLLMService(
            inner=inner,
            recorder=recorder,
            entity_type="blog_idea",
            entity_id="idea_004",
        )

        result, usage = service.generate_with_usage("blog_idea", {}, BlogIdea)
        assert usage["prompt_tokens"] == 0
        assert usage["completion_tokens"] == 0
        assert usage["total_tokens"] == 0

        runs = recorder.list_for_entity("blog_idea", "idea_004")
        assert len(runs) == 1
        assert runs[0].prompt_tokens == 0
        assert runs[0].completion_tokens == 0
        assert runs[0].total_tokens == 0

    def test_entity_type_and_id_passed_to_recorder(self) -> None:
        """Entity metadata is stored in the recorded run."""
        from backend.app.ai_runs import AiRunRepository
        from backend.app.llm.recording import RecordingLLMService

        expected = self.make_blog_idea()
        inner = FakeLLMService(responses={"blog_idea": expected})
        recorder = AiRunRepository()
        service = RecordingLLMService(
            inner=inner,
            recorder=recorder,
            entity_type="custom_entity",
            entity_id="custom_001",
            provider="test_provider",
            model="test-model",
        )

        service.generate("blog_idea", {}, BlogIdea)

        runs = recorder.list_for_entity("custom_entity", "custom_001")
        assert len(runs) == 1
        assert runs[0].entity_type == "custom_entity"
        assert runs[0].entity_id == "custom_001"
        assert runs[0].provider == "test_provider"
        assert runs[0].model == "test-model"


# ===========================================================================
# LLM Service — generate() helper, edge cases
# ===========================================================================


class TestLLMServiceEdgeCases:
    """Edge cases for LLMService ABC and FakeLLMService."""

    def test_generate_calls_generate_with_usage(self) -> None:
        """The generate() convenience method delegates to generate_with_usage."""
        expected = BlogIdea(
            title="Delegation Test",
            angle="Test",
            target_reader="Devs",
            article_goal="Test delegation",
        )
        service = FakeLLMService(responses={"blog_idea": expected})
        result = service.generate("blog_idea", {}, BlogIdea)
        assert result.title == "Delegation Test"

    def test_fake_service_generate_with_usage_returns_tokens(self) -> None:
        """FakeLLMService.generate_with_usage returns zeroed usage dict."""
        expected = BlogIdea(
            title="Token Test",
            angle="Test",
            target_reader="Devs",
            article_goal="Test tokens",
        )
        service = FakeLLMService(responses={"blog_idea": expected})
        result, usage = service.generate_with_usage("blog_idea", {}, BlogIdea)
        assert isinstance(result, BlogIdea)
        assert usage == {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    def test_fake_service_raises_on_empty_responses_dict(self) -> None:
        """Empty responses dict raises LLMGenerationError for any prompt."""
        service = FakeLLMService(responses={})
        with pytest.raises(LLMGenerationError, match="No fake response configured"):
            service.generate("any_prompt", {}, BlogIdea)

    def test_fake_service_error_message_lists_available(self) -> None:
        """Error message includes available prompt names."""
        expected = BlogIdea(
            title="Available",
            angle="Test",
            target_reader="Devs",
            article_goal="Test",
        )
        service = FakeLLMService(responses={"blog_idea": expected})
        with pytest.raises(LLMGenerationError, match="blog_idea"):
            service.generate("nonexistent", {}, BlogIdea)


# ===========================================================================
# Guardrails
# ===========================================================================


class TestClaimExtractionGuardrail:
    """Test the claim_extraction_guardrail factory."""

    @pytest.fixture(autouse=True)
    def _patch_agents_sdk(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Mock the Agents SDK module to avoid import errors."""
        import types

        mock_module = types.ModuleType("agents")

        class MockGuardrailFunctionOutput:
            def __init__(self, output_info: str = "", tripwire_triggered: bool = False):
                self.output_info = output_info
                self.tripwire_triggered = tripwire_triggered

        class MockOutputGuardrail:
            def __init__(self, func):
                self.func = func

        def mock_output_guardrail(*, name: str):
            def decorator(func):
                return MockOutputGuardrail(func)
            return decorator

        mock_module.GuardrailFunctionOutput = MockGuardrailFunctionOutput
        mock_module.OutputGuardrail = MockOutputGuardrail
        mock_module.output_guardrail = mock_output_guardrail
        monkeypatch.setitem(sys.modules, "agents", mock_module)

    def test_returns_output_guardrail(self) -> None:
        """Factory returns an OutputGuardrail instance."""
        from unittest.mock import MagicMock

        # Re-import guardrails after patching
        import importlib
        from backend.app.llm import guardrails
        importlib.reload(guardrails)

        claims_repo = MagicMock()
        ideas_repo = MagicMock()

        result = guardrails.claim_extraction_guardrail(
            claims_repository=claims_repo,
            ideas_repository=ideas_repo,
            idea_id="idea_001",
        )
        from agents import OutputGuardrail
        assert isinstance(result, OutputGuardrail)

    @pytest.mark.asyncio
    async def test_skips_when_no_idea_id(self) -> None:
        """Guardrail skips extraction when idea_id is empty."""
        from unittest.mock import MagicMock

        import importlib
        from backend.app.llm import guardrails
        importlib.reload(guardrails)

        claims_repo = MagicMock()
        ideas_repo = MagicMock()

        guardrail_fn = guardrails.claim_extraction_guardrail(
            claims_repository=claims_repo,
            ideas_repository=ideas_repo,
            idea_id="",
        )
        result = await guardrail_fn.func(None, None, None)
        from agents import GuardrailFunctionOutput
        assert isinstance(result, GuardrailFunctionOutput)
        assert result.tripwire_triggered is False
        assert "no idea_id" in result.output_info
        ideas_repo.get_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_idea_not_found(self) -> None:
        """Guardrail skips extraction when idea is not found."""
        from unittest.mock import MagicMock

        import importlib
        from backend.app.llm import guardrails
        importlib.reload(guardrails)

        claims_repo = MagicMock()
        ideas_repo = MagicMock()
        ideas_repo.get_by_id.return_value = None

        guardrail_fn = guardrails.claim_extraction_guardrail(
            claims_repository=claims_repo,
            ideas_repository=ideas_repo,
            idea_id="missing_idea",
        )
        result = await guardrail_fn.func(None, None, None)
        assert result.tripwire_triggered is False
        assert "no draft or idea not found" in result.output_info

    @pytest.mark.asyncio
    async def test_skips_when_draft_markdown_is_none(self) -> None:
        """Guardrail skips extraction when draft_markdown is None."""
        from unittest.mock import MagicMock

        import importlib
        from backend.app.llm import guardrails
        importlib.reload(guardrails)

        claims_repo = MagicMock()
        ideas_repo = MagicMock()
        mock_idea = MagicMock()
        mock_idea.draft_markdown = None
        ideas_repo.get_by_id.return_value = mock_idea

        guardrail_fn = guardrails.claim_extraction_guardrail(
            claims_repository=claims_repo,
            ideas_repository=ideas_repo,
            idea_id="idea_no_draft",
        )
        result = await guardrail_fn.func(None, None, None)
        assert result.tripwire_triggered is False
        assert "no draft or idea not found" in result.output_info

    @pytest.mark.asyncio
    async def test_extracts_and_stores_claims(self) -> None:
        """Guardrail extracts claims and stores them via repository."""
        from unittest.mock import MagicMock, patch

        import importlib
        from backend.app.llm import guardrails
        importlib.reload(guardrails)

        claims_repo = MagicMock()
        ideas_repo = MagicMock()
        mock_idea = MagicMock()
        mock_idea.draft_markdown = "# Test\n\nOur AI reduces cost by 80%."
        mock_idea.id = "idea_001"
        ideas_repo.get_by_id.return_value = mock_idea

        mock_claims = [{"type": "performance", "text": "reduces cost by 80%"}]

        with patch(
            "backend.app.blog_claims.heuristic_claims_from_draft",
            return_value=mock_claims,
        ):
            guardrail_fn = guardrails.claim_extraction_guardrail(
                claims_repository=claims_repo,
                ideas_repository=ideas_repo,
                idea_id="idea_001",
            )
            result = await guardrail_fn.func(None, None, None)

        assert result.tripwire_triggered is False
        assert "extracted 1 claims" in result.output_info
        claims_repo.replace_for_idea.assert_called_once_with("idea_001", mock_claims)

    @pytest.mark.asyncio
    async def test_skips_when_no_claims_found(self) -> None:
        """Guardrail skips storage when no claims are extracted."""
        from unittest.mock import MagicMock, patch

        import importlib
        from backend.app.llm import guardrails
        importlib.reload(guardrails)

        claims_repo = MagicMock()
        ideas_repo = MagicMock()
        mock_idea = MagicMock()
        mock_idea.draft_markdown = "Simple draft without claims."
        mock_idea.id = "idea_002"
        ideas_repo.get_by_id.return_value = mock_idea

        with patch(
            "backend.app.blog_claims.heuristic_claims_from_draft",
            return_value=[],
        ):
            guardrail_fn = guardrails.claim_extraction_guardrail(
                claims_repository=claims_repo,
                ideas_repository=ideas_repo,
                idea_id="idea_002",
            )
            result = await guardrail_fn.func(None, None, None)

        assert result.tripwire_triggered is False
        assert "extracted 0 claims" in result.output_info
        claims_repo.replace_for_idea.assert_not_called()
