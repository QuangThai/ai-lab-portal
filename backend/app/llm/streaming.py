"""Async streaming support for the Agents SDK LLM service.

Uses ``Runner.run_streamed()`` to stream agent output token-by-token via
Server-Sent Events (SSE), providing real-time generation visibility to the
admin UI.

Key design decisions:

- **Async generator**: The ``stream_generate()`` async generator yields SSE
  events (token deltas, completion, errors) that a FastAPI
  ``StreamingResponse`` can consume directly.
- **Hooks integration**: ``AiRunTimingHooks`` track per-agent and per-LLM-call
  timing, and the generator records the completed run to ``AiRunRepository``
  after the stream finishes.
- **Same agent construction**: The agent is built identically to the sync path
  in ``AgentsSDKLLMService.generate_with_usage()``, so outputs are compatible.
- **No Celery**: Streaming runs in the FastAPI event loop, not in a Celery
  worker. For long-running generations, consider a timeout or background task.
"""

from __future__ import annotations

from typing import Any, AsyncIterator

from agents import Agent, Runner, set_tracing_disabled
from agents.mcp import MCPServer
from agents.stream_events import (
    AgentUpdatedStreamEvent,
    RawResponsesStreamEvent,
    RunItemStreamEvent,
)
from openai.types.responses import (
    ResponseCompletedEvent,
    ResponseErrorEvent,
    ResponseFailedEvent,
    ResponseTextDeltaEvent,
    ResponseTextDoneEvent,
)
from pydantic import BaseModel

from backend.app.llm.hooks import AiRunTimingHooks
from backend.app.llm.prompts import PROMPT_REGISTRY
from backend.app.llm.service import LLMGenerationError

# Tracing is disabled by default; enable via setup_agents_tracing() at startup
set_tracing_disabled(True)

# ── SSE event types ───────────────────────────────────────────────────

SSE_EVENT_TYPES = {
    "token": "text delta token from the LLM",
    "done": "generation completed successfully",
    "result": "final structured output as JSON",
    "error": "an error occurred during generation",
    "status": "status update (e.g., guardrail running, session saving)",
}

# ── Streaming generator ───────────────────────────────────────────────


async def stream_generate(
    prompt_name: str,
    inputs: dict[str, Any],
    output_schema: type[BaseModel],
    model: str = "gpt-4o",
    recorder: Any = None,
    entity_id: str | None = None,
    entity_type: str = "",
    provider: str = "agents_sdk",
    mcp_servers: list[MCPServer] | None = None,
    agent: Agent | None = None,
) -> AsyncIterator[str]:
    """Run an agent with streaming and yield SSE-formatted events.

    Each yielded string is an SSE ``data:`` line (without the ``data:``
    prefix) that a FastAPI ``StreamingResponse`` can wrap.

    Args:
        prompt_name: Key into ``PROMPT_REGISTRY``.
        inputs: Dict of template variables for ``user_template.format()``.
        output_schema: Pydantic model class used as ``output_type``.
        model: OpenAI model name.
        recorder: Optional ``AiRunRepository`` for recording completed runs.
        entity_id: Entity ID for the recording.
        entity_type: Entity type for the recording.
        provider: Provider name for the recording.
        agent: Optional pre-built Agent. If provided, ``prompt_name`` and
            ``output_schema`` are ignored and this agent is used directly.

    Yields:
        SSE ``data:`` lines (without the prefix) as ``str``.
    """

    # If a pre-built agent is provided, use it directly
    if agent is not None:
        user = list(inputs.values())[0] if inputs else ""
    else:
        prompt = PROMPT_REGISTRY.get(prompt_name)
        if prompt is None:
            yield _sse_error(f"Unknown prompt '{prompt_name}'")
            return
        system = prompt.system
        user = prompt.user_template.format(**inputs)
        agent = Agent(
            name=prompt_name,
            instructions=system,
            model=model,
            output_type=output_schema,
            mcp_servers=mcp_servers or [],
        )

    # Lifecycle hooks for timing
    hooks = AiRunTimingHooks()
    accumulated_text: list[str] = []
    error_message: str | None = None

    try:
        yield _sse_status("starting_agent", f"Starting agent for '{prompt_name}'")

        result = await Runner.run_streamed(
            agent,
            user,
            hooks=hooks,
        )

        yield _sse_status("streaming", f"Streaming generation for '{prompt_name}'")

        # Iterate over stream events
        async for event in result.stream_events():
            if isinstance(event, RawResponsesStreamEvent):
                data = event.data

                if isinstance(data, ResponseTextDeltaEvent):
                    delta = data.delta
                    accumulated_text.append(delta)
                    yield _sse_token(delta)

                elif isinstance(data, ResponseTextDoneEvent):
                    yield _sse_status(
                        "text_done",
                        f"Text generation complete ({len(data.text)} chars)",
                    )

                elif isinstance(data, ResponseCompletedEvent):
                    yield _sse_status("response_complete", "Response completed")

                elif isinstance(data, ResponseErrorEvent):
                    error_message = f"Response error: {data.code}: {data.message}"
                    yield _sse_error(error_message)

                elif isinstance(data, ResponseFailedEvent):
                    error_message = f"Response failed: {data.code}: {data.message}"
                    yield _sse_error(error_message)

        # Check final output
        if error_message:
            # Already yielded error above; skip recording
            return

        parsed = result.final_output
        if not isinstance(parsed, output_schema):
            error_message = (
                f"Expected {output_schema.__name__}, "
                f"got {type(parsed).__name__}"
            )
            yield _sse_error(error_message)
            return

        yield _sse_status("saving_session", "Saving session state")

        # Record completed run to AiRunRepository
        if recorder is not None and entity_id:
            try:
                usage: dict[str, Any] = {}
                if result.usage is not None:
                    usage["prompt_tokens"] = result.usage.input_tokens
                    usage["completion_tokens"] = result.usage.output_tokens
                    usage["total_tokens"] = (
                        result.usage.input_tokens + result.usage.output_tokens
                    )

                recorder.record_completed(
                    prompt_name=prompt_name,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    provider=provider,
                    model=model,
                    input_payload=inputs,
                    output_payload=parsed.model_dump(),
                    prompt_tokens=usage.get("prompt_tokens"),
                    completion_tokens=usage.get("completion_tokens"),
                    total_tokens=usage.get("total_tokens"),
                    latency_ms=hooks.total_ms,
                )
            except Exception as exc:
                # Recording failure is non-fatal
                yield _sse_status("record_warning", f"Recording failed: {exc}")

        # Yield final result
        yield _sse_result(parsed.model_dump())

    except LLMGenerationError:
        yield _sse_error("LLM generation failed")
    except Exception as exc:
        yield _sse_error(f"Streaming error: {exc}")


# ── SSE formatting helpers ────────────────────────────────────────────


def _sse_token(delta: str) -> str:
    """Format a token delta SSE event."""
    import json

    return json.dumps({"type": "token", "data": delta})


def _sse_done() -> str:
    """Format a completion SSE event."""
    import json

    return json.dumps({"type": "done", "data": "generation_complete"})


def _sse_result(data: dict[str, Any]) -> str:
    """Format a final result SSE event."""
    import json

    return json.dumps({"type": "result", "data": data})


def _sse_error(message: str) -> str:
    """Format an error SSE event."""
    import json

    return json.dumps({"type": "error", "data": message})


def _sse_status(status: str, message: str) -> str:
    """Format a status update SSE event."""
    import json

    return json.dumps({"type": "status", "status": status, "data": message})
