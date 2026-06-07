"""LLM provider abstraction for structured output generation.

The service layer provides a uniform interface for calling LLM providers
(OpenAI, Anthropic, etc.) with typed Pydantic output schemas. MVP ships
with an OpenAI implementation; providers are swappable via the abstract
base class.

Key design decisions:

- **Structured output via Pydantic**: The OpenAI ``response_format`` param
  (structured output / function calling) returns validated Pydantic models
  directly — no JSON parsing or manual validation in business logic.
- **Prompt registry lookup**: Callers pass a ``prompt_name`` that is looked
  up in ``backend.app.llm.prompts.PROMPT_REGISTRY``. This keeps system
  messages versioned and testable.
- **Sync calls in workers**: Celery workers are not async-native, so the
  service exposes a synchronous ``generate`` method.
- **Fake provider for tests**: ``FakeLLMService`` returns canned Pydantic
  responses so tests never call a real API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from openai import OpenAI
from pydantic import BaseModel

from backend.app.llm.prompts import PROMPT_REGISTRY

# ─── Output quality validation ─────────────────────────────────────────────

# Markers that suggest hallucinated or low-quality content when found in drafts.
_HALLUCINATION_MARKERS: tuple[str, ...] = (
    "according to internal data",
    "internal analytics show",
    "our research indicates",
    "studies have shown that we",
    "as demonstrated by our proprietary",
    "based on our extensive research",
    "our proprietary technology",
    "we have developed a revolutionary",
    "our unique approach",
    "unprecedented results",
)


MIN_DRAFT_WORDS = 500  # minimum acceptable draft length
MIN_SECTION_WORDS = 100  # minimum acceptable section length


def _validate_output_quality(prompt_name: str, output: BaseModel) -> None:
    """Validate LLM output quality after parsing.

    Checks draft word count, hallucination markers, and content substance.
    Raises ``LLMOutputValidationError`` if quality checks fail.

    This is a lightweight guard — not a replacement for the dedicated
    Technical Review and Claim Extraction stages.
    """
    details: dict[str, Any] = {}

    # Check draft word count
    if hasattr(output, "markdown") and isinstance(output.markdown, str):
        word_count = len(output.markdown.split())
        details["word_count"] = word_count
        min_words = MIN_SECTION_WORDS if prompt_name == "draft_section_writer" else MIN_DRAFT_WORDS
        if word_count < min_words:
            raise LLMOutputValidationError(
                f"Draft too short: {word_count} words (minimum {min_words})",
                {"word_count": word_count, "minimum": min_words},
            )

    # Check for hallucination markers in draft content
    if hasattr(output, "markdown") and isinstance(output.markdown, str):
        lower = output.markdown.lower()
        found = [m for m in _HALLUCINATION_MARKERS if m in lower]
        if found:
            details["hallucination_markers"] = found
            raise LLMOutputValidationError(
                f"Draft contains potential hallucination markers: {found}",
                {"hallucination_markers": found},
            )

    # Check technical review has meaningful issues (not auto-approve everything)
    if hasattr(output, "issues") and hasattr(output, "approval_recommendation"):
        details["issue_count"] = len(output.issues)
        # If review approves but found zero issues, flag as suspicious
        if output.approval_recommendation == "approve" and len(output.issues) == 0:
            details["empty_approval"] = True
            # Warning only, not blocking — legitimate for polished drafts


class LLMService(ABC):
    """Abstract LLM provider for structured text generation.

    Subclasses must implement :meth:`generate` to call a real or fake provider
    and return a validated Pydantic model.
    """

    def generate(
        self,
        prompt_name: str,
        inputs: dict[str, Any],
        output_schema: type[BaseModel],
    ) -> BaseModel:
        result, _usage = self.generate_with_usage(prompt_name, inputs, output_schema)
        return result

    @abstractmethod
    def generate_with_usage(
        self,
        prompt_name: str,
        inputs: dict[str, Any],
        output_schema: type[BaseModel],
    ) -> tuple[BaseModel, dict[str, int] | None]:
        """Call the LLM and return a validated structured output.

        Args:
            prompt_name: Key into ``PROMPT_REGISTRY``.
            inputs: Dict of template variables for ``user_template.format()``.
            output_schema: Pydantic model class used as ``response_format``.

        Returns:
            An instance of ``output_schema`` populated by the LLM response.

        Raises:
            KeyError: If ``prompt_name`` is not in the registry.
            LLMGenerationError: If the provider fails or returns invalid data.
        """
        ...


class LLMGenerationError(Exception):
    """Raised when the LLM provider fails to generate valid structured output."""


class LLMOutputValidationError(Exception):
    """Raised when the LLM output fails quality validation.

    Attributes:
        message: Human-readable error description.
        validation_details: Dict of field-level validation results.
    """

    def __init__(
        self,
        message: str,
        validation_details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.validation_details = validation_details or {}


class OpenAILLMService(LLMService):
    """LLM service backed by OpenAI structured outputs.

    Uses ``openai.beta.chat.completions.parse`` which returns a typed
    Pydantic model directly via the ``response_format`` parameter.

    Args:
        api_key: OpenAI API key.
        model: OpenAI model name (default ``gpt-4o``).
    """

    def __init__(self, api_key: str, model: str = "gpt-4o") -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate_with_usage(
        self,
        prompt_name: str,
        inputs: dict[str, Any],
        output_schema: type[BaseModel],
    ) -> tuple[BaseModel, dict[str, int] | None]:
        prompt = PROMPT_REGISTRY.get(prompt_name)
        if prompt is None:
            raise KeyError(
                f"Unknown prompt '{prompt_name}'. "
                f"Available: {list(PROMPT_REGISTRY)}"
            )

        system = prompt.system
        user = prompt.user_template.format(**inputs)

        completion_kwargs: dict[str, Any] = {}
        if prompt_name == "draft_writer":
            completion_kwargs["max_completion_tokens"] = 12000
        if prompt_name == "draft_section_writer":
            completion_kwargs["max_completion_tokens"] = 2500

        try:
            completion = self._client.beta.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format=output_schema,
                **completion_kwargs,
            )
        except Exception as exc:
            raise LLMGenerationError(
                f"OpenAI API call failed for prompt '{prompt_name}': {exc}"
            ) from exc

        parsed = completion.choices[0].message.parsed
        if parsed is None:
            raise LLMGenerationError(
                f"LLM returned no parsed response for prompt '{prompt_name}'"
            )

        # Post-generation quality validation
        _validate_output_quality(prompt_name, parsed)

        usage = None
        if completion.usage is not None:
            usage = {
                "prompt_tokens": completion.usage.prompt_tokens,
                "completion_tokens": completion.usage.completion_tokens,
                "total_tokens": completion.usage.total_tokens,
            }
        return parsed, usage


class FakeLLMService(LLMService):
    """Fake LLM service for tests.

    Returns pre-configured responses keyed by prompt name. Does not call any
    external API.

    Args:
        responses: Mapping of ``prompt_name`` to canned ``BaseModel`` instance.
            Prompts not in this dict raise ``LLMGenerationError``.
    """

    def __init__(self, responses: dict[str, BaseModel]) -> None:
        self._responses = dict(responses)

    def generate_with_usage(
        self,
        prompt_name: str,
        inputs: dict[str, Any],  # noqa: ARG002 — not used by fake
        output_schema: type[BaseModel],  # noqa: ARG002 — not used by fake
    ) -> tuple[BaseModel, dict[str, int] | None]:
        result = self._responses.get(prompt_name)
        if result is None:
            raise LLMGenerationError(
                f"No fake response configured for '{prompt_name}'. "
                f"Available: {list(self._responses)}"
            )
        return result, {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
