"""Wraps an LLM service to persist AI run metadata."""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel

from backend.app.ai_runs import AiRunRepository
from backend.app.llm.service import LLMGenerationError, LLMService


class RecordingLLMService(LLMService):
    def __init__(
        self,
        inner: LLMService,
        recorder: AiRunRepository,
        *,
        entity_type: str,
        entity_id: str,
        provider: str = "openai",
        model: str = "gpt-4o",
    ) -> None:
        self._inner = inner
        self._recorder = recorder
        self._entity_type = entity_type
        self._entity_id = entity_id
        self._provider = provider
        self._model = model

    def generate_with_usage(
        self,
        prompt_name: str,
        inputs: dict[str, Any],
        output_schema: type[BaseModel],
    ) -> tuple[BaseModel, dict[str, int] | None]:
        started = time.perf_counter()
        try:
            result, usage = self._inner.generate_with_usage(
                prompt_name, inputs, output_schema
            )
        except LLMGenerationError as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            self._recorder.record_failed(
                prompt_name=prompt_name,
                entity_type=self._entity_type,
                entity_id=self._entity_id,
                provider=self._provider,
                model=self._model,
                input_payload=inputs,
                error_message=str(exc),
                latency_ms=latency_ms,
            )
            raise
        except Exception as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            self._recorder.record_failed(
                prompt_name=prompt_name,
                entity_type=self._entity_type,
                entity_id=self._entity_id,
                provider=self._provider,
                model=self._model,
                input_payload=inputs,
                error_message=str(exc),
                latency_ms=latency_ms,
            )
            raise LLMGenerationError(str(exc)) from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        self._recorder.record_completed(
            prompt_name=prompt_name,
            entity_type=self._entity_type,
            entity_id=self._entity_id,
            provider=self._provider,
            model=self._model,
            input_payload=inputs,
            output_payload=result.model_dump(),
            prompt_tokens=usage.get("prompt_tokens") if usage else None,
            completion_tokens=usage.get("completion_tokens") if usage else None,
            total_tokens=usage.get("total_tokens") if usage else None,
            latency_ms=latency_ms,
        )
        return result, usage
