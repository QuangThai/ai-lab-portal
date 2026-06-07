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
- **Native output guardrails**: Guardrails use the Agents SDK's
  ``@output_guardrail`` decorator and are passed directly to
  ``Agent(output_guardrails=[...])``.
- **Native lifecycle hooks**: ``AiRunTimingHooks`` replace the
  ``RecordingLLMService`` wrapper pattern. The hooks track per-agent and
  per-LLM-call timing, and ``generate_with_usage`` records the combined
  timing + result data to ``AiRunRepository``.
- **Token usage**: The Agents SDK returns token usage on ``result.usage``.
- **Backward compatible**: Output shape (Pydantic model) is identical to
  ``OpenAILLMService``, so callers see no difference.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from agents import Agent, OutputGuardrail, Runner, set_tracing_disabled
from agents.mcp import MCPServer
from agents import trace as agents_trace
from agents.run import RunConfig
from pydantic import BaseModel

from backend.app.llm.hooks import AiRunTimingHooks
from backend.app.llm.prompts import PROMPT_REGISTRY
from backend.app.llm.service import LLMGenerationError, LLMService

if TYPE_CHECKING:
    from backend.app.ai_runs import AiRunRepository
    from backend.app.llm.sessions import AgentSessionStore

# Tracing is disabled globally by default. When using the Agents SDK backend,
# call ``setup_agents_tracing()`` at app startup to enable tracing with the
# custom ``AiRunSpanProcessor``. Per-run tracing can be toggled via RunConfig.
set_tracing_disabled(True)


class AgentsSDKLLMService(LLMService):
    """LLM service backed by the OpenAI Agents SDK.

    Each call to ``generate_with_usage`` creates an ``Agent`` on the fly from
    the prompt registry entry and runs it synchronously via ``Runner.run_sync``.
    Native Agents SDK output guardrails and lifecycle hooks are passed to the
    Agent and Runner respectively.

    When a recorder is provided, the service records run metadata to
    ``AiRunRepository`` using timing data from ``AiRunTimingHooks`` combined
    with result data (usage, output, trace_id) from ``Runner.run_sync``.

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
        recorder: AiRunRepository | None = None,
        entity_type: str = "",
        provider: str = "agents_sdk",
        mcp_servers: list[MCPServer] | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._session_store = session_store
        self._entity_id = entity_id
        self._recorder = recorder
        self._entity_type = entity_type
        self._provider = provider
        self._mcp_servers = mcp_servers
        # Maps prompt_name -> list of native OutputGuardrail objects
        self._output_guardrails: dict[str, list[OutputGuardrail]] = {}

    # ── Guardrail registration ──────────────────────────────────────────

    def add_output_guardrail(self, prompt_name: str, guardrail: OutputGuardrail) -> None:
        """Register a native Agents SDK output guardrail for a prompt.

        The guardrail will be passed to ``Agent(output_guardrails=...)`` on
        the next ``generate_with_usage`` call for this prompt name.

        Args:
            prompt_name: Key into ``PROMPT_REGISTRY``.
            guardrail: An ``OutputGuardrail`` created via ``@output_guardrail``.
        """
        if prompt_name not in self._output_guardrails:
            self._output_guardrails[prompt_name] = []
        self._output_guardrails[prompt_name].append(guardrail)

    def add_guardrail(self, prompt_name: str, guardrail: Any) -> None:
        """Deprecated: use ``add_output_guardrail`` instead."""
        if prompt_name not in self._output_guardrails:
            self._output_guardrails[prompt_name] = []
        if isinstance(guardrail, OutputGuardrail):
            self._output_guardrails[prompt_name].append(guardrail)
        else:
            from agents.guardrail import OutputGuardrail as _OG

            self._output_guardrails[prompt_name].append(
                _OG(
                    guardrail_function=guardrail,
                    name=f"{prompt_name}_legacy_guardrail",
                )
            )

    # ── Generation ──────────────────────────────────────────────────────

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

        # Collect native output guardrails registered for this prompt
        prompt_guardrails = self._output_guardrails.get(prompt_name, [])

        # Create an Agent for this pipeline stage with native guardrails
        # and optional MCP servers for tool access
        agent = Agent(
            name=prompt_name,
            instructions=system,
            model=self._model,
            output_type=output_schema,
            output_guardrails=prompt_guardrails if prompt_guardrails else None,
            mcp_servers=self._mcp_servers,
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

        # Create lifecycle hooks for timing
        hooks = AiRunTimingHooks()

        try:
            with agents_trace(
                workflow_name=f"blog_{prompt_name}",
                trace_id=run_config.trace_id,
                metadata=run_config.trace_metadata,
            ):
                result = Runner.run_sync(
                    agent,
                    user,
                    hooks=hooks,
                    run_config=run_config,
                    **run_kwargs,
                )
        except Exception as exc:
            # Record failure using hooks timing
            if self._recorder and self._entity_id:
                self._recorder.record_failed(
                    prompt_name=prompt_name,
                    entity_type=self._entity_type,
                    entity_id=self._entity_id,
                    provider=self._provider,
                    model=self._model,
                    input_payload=inputs,
                    error_message=str(exc),
                    latency_ms=hooks.total_ms,
                )
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
                pass

        parsed = result.final_output
        if not isinstance(parsed, output_schema):
            raise LLMGenerationError(
                f"Agents SDK returned unexpected type for prompt '{prompt_name}': "
                f"{type(parsed).__name__}"
            )

        # Build usage dict from result
        usage: dict[str, Any] = {}
        if result.usage is not None:
            usage["prompt_tokens"] = result.usage.input_tokens
            usage["completion_tokens"] = result.usage.output_tokens
            usage["total_tokens"] = (
                result.usage.input_tokens + result.usage.output_tokens
            )
        usage["trace_id"] = run_config.trace_id

        # Record completed run using hooks timing + result data
        if self._recorder and self._entity_id:
            self._recorder.record_completed(
                prompt_name=prompt_name,
                entity_type=self._entity_type,
                entity_id=self._entity_id,
                provider=self._provider,
                model=self._model,
                input_payload=inputs,
                output_payload=parsed.model_dump(),
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
                total_tokens=usage.get("total_tokens"),
                latency_ms=hooks.total_ms,
                trace_id=run_config.trace_id,
            )

        return parsed, usage
