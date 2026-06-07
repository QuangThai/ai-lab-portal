"""LLM service backed by the OpenAI Agents SDK.

Wraps ``openai-agents`` ``Agent`` + ``Runner.run_sync`` behind the existing
``LLMService`` ABC so the blog pipeline can switch between direct OpenAI SDK
calls and Agents SDK orchestration via the ``AI_LAB_LLM_BACKEND`` env var.

Key design decisions:

- **Prompt registry integration**: Each pipeline stage becomes an ``Agent``
  with ``instructions`` from ``PROMPT_REGISTRY`` and ``output_type`` from the
  existing Pydantic schemas. This keeps prompts versioned and testable.
- **Synchronous API**: Celery workers are not async-native, so we use
  ``Runner.run_sync()`` and disable tracing by default (agents SDK tracing
  can be enabled independently via the env).
- **Token usage**: The Agents SDK returns token usage on ``result.usage``.
- **Backward compatible**: Output shape (Pydantic model) is identical to
  ``OpenAILLMService``, so callers see no difference.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from agents import Agent, Runner, set_tracing_disabled
from agents import trace as agents_trace
from agents.run import RunConfig
from pydantic import BaseModel

from backend.app.llm.prompts import PROMPT_REGISTRY
from backend.app.llm.service import LLMGenerationError, LLMService

if TYPE_CHECKING:
    from backend.app.llm.sessions import AgentSessionStore

# Tracing is disabled globally by default. When using the Agents SDK backend,
# call ``setup_agents_tracing()`` at app startup to enable tracing with the
# custom ``AiRunSpanProcessor``. Per-run tracing can be toggled via RunConfig.
set_tracing_disabled(True)


class AgentsSDKLLMService(LLMService):
    """LLM service backed by the OpenAI Agents SDK.

    Each call to ``generate_with_usage`` creates an ``Agent`` on the fly from
    the prompt registry entry and runs it synchronously via ``Runner.run_sync``.

    Args:
        api_key: OpenAI API key.
        model: OpenAI model name (default ``gpt-4o``).
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        session_store: AgentSessionStore | None = None,
        entity_id: str | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._session_store = session_store
        self._entity_id = entity_id
        self._guardrails: dict[
            str, list[Any]
        ] = {}  # prompt_name -> list of guardrails

    def add_guardrail(self, prompt_name: str, guardrail: Any) -> None:
        """Register a post-generation hook for a prompt."""
        if prompt_name not in self._guardrails:
            self._guardrails[prompt_name] = []
        self._guardrails[prompt_name].append(guardrail)

    def _run_guardrails(self, prompt_name: str, output: Any, inputs: dict[str, Any]) -> None:
        for guardrail in self._guardrails.get(prompt_name, []):
            try:
                guardrail(output, inputs)
            except Exception:
                pass

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

        # Create an Agent for this pipeline stage
        agent = Agent(
            name=prompt_name,
            instructions=system,
            model=self._model,
            output_type=output_schema,
        )

        # Enable tracing for this run via RunConfig
        from agents.util import gen_trace_id

        run_config = RunConfig(
            workflow_name=f"blog_{prompt_name}",
            trace_id=gen_trace_id(),
            trace_metadata={
                "prompt_name": prompt_name,
                "model": self._model,
            },
        )

        # Longer context window for draft generation
        run_kwargs: dict[str, Any] = {}
        if prompt_name in ("draft_writer", "draft_section_writer"):
            run_kwargs["max_tokens"] = 16000

        try:
            with agents_trace(
                workflow_name=f"blog_{prompt_name}",
                trace_id=run_config.trace_id,
                metadata=run_config.trace_metadata,
            ):
                result = Runner.run_sync(
                    agent,
                    user,
                    run_config=run_config,
                    **run_kwargs,
                )
        except Exception as exc:
            raise LLMGenerationError(
                f"Agents SDK call failed for prompt '{prompt_name}': {exc}"
            ) from exc

        # Save session state for HITL resumption
        if self._session_store is not None and self._entity_id:
            try:
                state = result.to_state()
                self._session_store.save(
                    self._entity_id,
                    state,
                    agent_name=prompt_name,
                    metadata={"prompt_name": prompt_name, "model": self._model},
                )
            except Exception:
                # Session save is best-effort; don't break the generation
                pass

        parsed = result.final_output
        if not isinstance(parsed, output_schema):
            raise LLMGenerationError(
                f"Agents SDK returned unexpected type for prompt '{prompt_name}': "
                f"{type(parsed).__name__}"
            )

        # Run registered post-generation guardrails
        self._run_guardrails(prompt_name, parsed, inputs)

        usage: dict[str, Any] = {}
        if result.usage is not None:
            usage["prompt_tokens"] = result.usage.input_tokens
            usage["completion_tokens"] = result.usage.output_tokens
            usage["total_tokens"] = (
                result.usage.input_tokens + result.usage.output_tokens
            )

        # Include the Agents SDK trace ID so RecordingLLMService can persist it
        usage["trace_id"] = run_config.trace_id

        return parsed, usage
