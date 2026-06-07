"""Custom tracing processor for OpenAI Agents SDK spans.

Wires Agent SDK traces and spans into the application logging system and
prepares for future persistence to the ``ai_runs`` table.

Usage in ``AgentsSDKLLMService``::

    from backend.app.llm.tracing import setup_agents_tracing, AiRunSpanProcessor

    processor = AiRunSpanProcessor()
    setup_agents_tracing(processor)
    # Or add via add_trace_processor(processor)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from agents.tracing import add_trace_processor, set_trace_processors
from agents.tracing.processor_interface import TracingProcessor

if TYPE_CHECKING:
    from agents.tracing.spans import Span
    from agents.tracing.traces import Trace

logger = logging.getLogger(__name__)


class AiRunSpanProcessor(TracingProcessor):
    """Custom tracing processor that logs Agent SDK spans.

    Records trace and span lifecycle events to the application logger.
    Designed to be extended for writing to the ``ai_runs`` table.

    Attributes:
        active_traces: Mapping of trace_id to trace metadata (completed on finish).
        active_spans: Mapping of span_id to span metadata (completed on finish).
    """

    def __init__(self) -> None:
        self.active_traces: dict[str, dict[str, Any]] = {}
        self.active_spans: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Trace lifecycle
    # ------------------------------------------------------------------

    def on_trace_start(self, trace: "Trace") -> None:
        self.active_traces[trace.trace_id] = {
            "trace_id": trace.trace_id,
            "workflow_name": trace.name,
            "group_id": trace.group_id,
            "metadata": trace.metadata,
            "started": True,
        }
        logger.debug(
            "Agent trace started: %s (id=%s, group=%s)",
            trace.name,
            trace.trace_id,
            trace.group_id,
        )

    def on_trace_end(self, trace: "Trace") -> None:
        entry = self.active_traces.pop(trace.trace_id, {})
        entry["completed"] = True
        logger.info(
            "Agent trace completed: %s (id=%s, spans=%d)",
            trace.name,
            trace.trace_id,
            len(self.active_spans),
        )

    # ------------------------------------------------------------------
    # Span lifecycle
    # ------------------------------------------------------------------

    def on_span_start(self, span: "Span") -> None:
        self.active_spans[span.span_id] = {
            "span_id": span.span_id,
            "trace_id": span.trace_id,
            "type": span.type,
            "name": span.name,
            "started": True,
        }
        logger.debug(
            "Span started: %s (id=%s, type=%s)",
            span.name,
            span.span_id,
            span.type,
        )

    def on_span_end(self, span: "Span") -> None:
        entry = self.active_spans.pop(span.span_id, {})
        logger.debug(
            "Span completed: %s (id=%s)",
            span.name,
            span.span_id,
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def shutdown(self) -> None:
        self.active_traces.clear()
        self.active_spans.clear()
        logger.debug("AiRunSpanProcessor shut down")

    def force_flush(self) -> None:
        pass


def setup_agents_tracing(
    processor: TracingProcessor | None = None,
    disabled: bool = False,
) -> None:
    """Configure the Agents SDK tracing system.

    Call once at application startup when using the Agents SDK backend.

    Args:
        processor: Custom processor (defaults to ``AiRunSpanProcessor``).
        disabled: If True, globally disable tracing (overrides processor).
    """
    from agents.tracing import set_tracing_disabled

    set_tracing_disabled(disabled)
    if not disabled:
        actual = processor or AiRunSpanProcessor()
        set_trace_processors([actual])
        logger.info(
            "Agents SDK tracing enabled with %s",
            type(actual).__name__,
        )
