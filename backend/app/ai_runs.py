"""Persistence for AI run metadata (provider, model, prompt version, tokens)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy import Engine, insert, select

from backend.app.database import ai_runs as ai_runs_table
from backend.app.llm.prompts import PROMPT_REGISTRY

AiRunStatus = Literal["completed", "failed"]


class AiRun(BaseModel):
    id: str
    prompt_name: str
    prompt_version: str
    entity_type: str
    entity_id: str
    provider: str
    model: str
    status: AiRunStatus
    input_payload: dict[str, Any]
    output_payload: dict[str, Any] | None = None
    error_message: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    latency_ms: int | None = None
    created_at: datetime


class AiRunRepository:
    def __init__(self) -> None:
        self._runs: dict[str, AiRun] = {}

    def record_completed(
        self,
        *,
        prompt_name: str,
        entity_type: str,
        entity_id: str,
        provider: str,
        model: str,
        input_payload: dict[str, Any],
        output_payload: dict[str, Any],
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
        latency_ms: int | None = None,
    ) -> AiRun:
        prompt = PROMPT_REGISTRY.get(prompt_name)
        version = prompt.version if prompt is not None else "0"
        run = AiRun(
            id=f"airun_{uuid4().hex}",
            prompt_name=prompt_name,
            prompt_version=version,
            entity_type=entity_type,
            entity_id=entity_id,
            provider=provider,
            model=model,
            status="completed",
            input_payload=input_payload,
            output_payload=output_payload,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            created_at=datetime.now(UTC),
        )
        self._runs[run.id] = run
        return run

    def record_failed(
        self,
        *,
        prompt_name: str,
        entity_type: str,
        entity_id: str,
        provider: str,
        model: str,
        input_payload: dict[str, Any],
        error_message: str,
        latency_ms: int | None = None,
    ) -> AiRun:
        prompt = PROMPT_REGISTRY.get(prompt_name)
        version = prompt.version if prompt is not None else "0"
        run = AiRun(
            id=f"airun_{uuid4().hex}",
            prompt_name=prompt_name,
            prompt_version=version,
            entity_type=entity_type,
            entity_id=entity_id,
            provider=provider,
            model=model,
            status="failed",
            input_payload=input_payload,
            error_message=error_message[:2000],
            latency_ms=latency_ms,
            created_at=datetime.now(UTC),
        )
        self._runs[run.id] = run
        return run

    def list_for_entity(self, entity_type: str, entity_id: str) -> list[AiRun]:
        items = [
            r
            for r in self._runs.values()
            if r.entity_type == entity_type and r.entity_id == entity_id
        ]
        items.sort(key=lambda r: r.created_at, reverse=True)
        return items


class PostgresAiRunRepository(AiRunRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def record_completed(
        self,
        *,
        prompt_name: str,
        entity_type: str,
        entity_id: str,
        provider: str,
        model: str,
        input_payload: dict[str, Any],
        output_payload: dict[str, Any],
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
        latency_ms: int | None = None,
    ) -> AiRun:
        prompt = PROMPT_REGISTRY.get(prompt_name)
        version = prompt.version if prompt is not None else "0"
        now = datetime.now(UTC)
        run_id = f"airun_{uuid4().hex}"
        data = {
            "id": run_id,
            "prompt_name": prompt_name,
            "prompt_version": version,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "provider": provider,
            "model": model,
            "status": "completed",
            "input_payload": json.dumps(input_payload),
            "output_payload": json.dumps(output_payload),
            "error_message": None,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "latency_ms": latency_ms,
            "created_at": now,
        }
        with self._engine.begin() as conn:
            conn.execute(insert(ai_runs_table).values(**data))
        return AiRun(
            **{
                **data,
                "input_payload": input_payload,
                "output_payload": output_payload,
            }
        )

    def record_failed(
        self,
        *,
        prompt_name: str,
        entity_type: str,
        entity_id: str,
        provider: str,
        model: str,
        input_payload: dict[str, Any],
        error_message: str,
        latency_ms: int | None = None,
    ) -> AiRun:
        prompt = PROMPT_REGISTRY.get(prompt_name)
        version = prompt.version if prompt is not None else "0"
        now = datetime.now(UTC)
        run_id = f"airun_{uuid4().hex}"
        data = {
            "id": run_id,
            "prompt_name": prompt_name,
            "prompt_version": version,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "provider": provider,
            "model": model,
            "status": "failed",
            "input_payload": json.dumps(input_payload),
            "output_payload": None,
            "error_message": error_message[:2000],
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
            "latency_ms": latency_ms,
            "created_at": now,
        }
        with self._engine.begin() as conn:
            conn.execute(insert(ai_runs_table).values(**data))
        return AiRun(**{**data, "input_payload": input_payload, "output_payload": None})

    def list_for_entity(self, entity_type: str, entity_id: str) -> list[AiRun]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                select(ai_runs_table)
                .where(
                    ai_runs_table.c.entity_type == entity_type,
                    ai_runs_table.c.entity_id == entity_id,
                )
                .order_by(ai_runs_table.c.created_at.desc())
            ).mappings()
            return [_row_to_run(dict(row)) for row in rows]


def _row_to_run(data: dict) -> AiRun:
    raw_in = data.pop("input_payload", "{}")
    raw_out = data.pop("output_payload", None)
    try:
        data["input_payload"] = json.loads(raw_in) if raw_in else {}
    except json.JSONDecodeError:
        data["input_payload"] = {}
    if raw_out:
        try:
            data["output_payload"] = json.loads(raw_out)
        except json.JSONDecodeError:
            data["output_payload"] = None
    else:
        data["output_payload"] = None
    return AiRun(**data)
