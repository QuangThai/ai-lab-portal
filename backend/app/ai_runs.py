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
from backend.app.pricing import compute_cost

AiRunStatus = Literal["completed", "failed"]


class CostStats(BaseModel):
    total_cost: float
    avg_cost_per_run: float
    cost_by_model: dict[str, float]
    cost_by_stage: dict[str, float]
    cost_by_month: dict[str, float]
    top_entities: list[dict[str, Any]]


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
    trace_id: str | None = None
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
        trace_id: str | None = None,
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
            trace_id=trace_id,
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
        trace_id: str | None = None,
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
            trace_id=trace_id,
            created_at=datetime.now(UTC),
        )
        self._runs[run.id] = run
        return run

    def list_latest(
        self, limit: int = 50, entity_type: str | None = None
    ) -> list[AiRun]:
        """Return the most recent runs, optionally filtered by entity type."""
        items = self._runs.values()
        if entity_type:
            items = [r for r in items if r.entity_type == entity_type]
        sorted_items = sorted(items, key=lambda r: r.created_at, reverse=True)
        return sorted_items[:limit]

    def get_stats(
        self, entity_type: str | None = None
    ) -> dict[str, Any]:
        """Compute aggregate stats, optionally filtered by entity type."""
        runs = list(self._runs.values())
        if entity_type:
            runs = [r for r in runs if r.entity_type == entity_type]
        total = len(runs)
        completed = sum(1 for r in runs if r.status == "completed")
        failed = total - completed

        prompt_names = set(r.prompt_name for r in runs)

        completed_runs = [r for r in runs if r.status == "completed"]
        avg_latency = 0.0
        avg_tokens = 0.0
        total_tokens = 0
        if completed_runs:
            latencies = [r.latency_ms for r in completed_runs if r.latency_ms is not None]
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
            token_list = [
                r.total_tokens for r in completed_runs if r.total_tokens is not None
            ]
            if token_list:
                total_tokens = sum(token_list)
                avg_tokens = total_tokens / len(token_list)

        # Per-stage stats
        stage_stats: dict[str, dict[str, Any]] = {}
        for name in sorted(prompt_names):
            stage_runs = [r for r in completed_runs if r.prompt_name == name]
            stage_latencies = [
                r.latency_ms for r in stage_runs if r.latency_ms is not None
            ]
            stage_tokens = [r.total_tokens for r in stage_runs if r.total_tokens is not None]
            stage_stats[name] = {
                "count": len(stage_runs),
                "avg_latency_ms": round(sum(stage_latencies) / len(stage_latencies), 1)
                if stage_latencies
                else 0,
                "avg_total_tokens": round(sum(stage_tokens) / len(stage_tokens), 1)
                if stage_tokens
                else 0,
                "total_tokens": sum(stage_tokens),
            }

        return {
            "total_runs": total,
            "completed": completed,
            "failed": failed,
            "success_rate": round(completed / total * 100, 1) if total else 0.0,
            "avg_latency_ms": round(avg_latency, 1),
            "avg_total_tokens": round(avg_tokens, 1),
            "total_tokens": total_tokens,
            "stages": stage_stats,
        }

    def get_cost_stats(self) -> CostStats:
        """Return cost breakdown from in-memory runs."""
        completed = [r for r in self._runs.values() if r.status == "completed"]
        if not completed:
            return CostStats(
                total_cost=0.0,
                avg_cost_per_run=0.0,
                cost_by_model={},
                cost_by_stage={},
                cost_by_month={},
                top_entities=[],
            )

        total_cost = 0.0
        cost_by_model: dict[str, float] = {}
        cost_by_stage: dict[str, float] = {}
        cost_by_month: dict[str, float] = {}
        entity_costs: dict[str, float] = {}

        for run in completed:
            cost = compute_cost(run.prompt_tokens, run.completion_tokens, run.model)
            total_cost += cost

            model_key = run.model or "unknown"
            cost_by_model[model_key] = cost_by_model.get(model_key, 0.0) + cost

            cost_by_stage[run.prompt_name] = cost_by_stage.get(run.prompt_name, 0.0) + cost

            if run.latency_ms is not None:
                month_key = run.created_at.strftime("%Y-%m")
                cost_by_month[month_key] = cost_by_month.get(month_key, 0.0) + cost

            entity_key = f"{run.entity_type}:{run.entity_id}"
            entity_costs[entity_key] = entity_costs.get(entity_key, 0.0) + cost

        # Top 10 entities
        sorted_entities = sorted(
            [{"entity": k, "cost": round(v, 4)} for k, v in entity_costs.items()],
            key=lambda x: x["cost"],
            reverse=True,
        )[:10]

        return CostStats(
            total_cost=round(total_cost, 4),
            avg_cost_per_run=round(total_cost / len(completed), 4),
            cost_by_model={k: round(v, 4) for k, v in cost_by_model.items()},
            cost_by_stage={k: round(v, 4) for k, v in cost_by_stage.items()},
            cost_by_month={k: round(v, 4) for k, v in cost_by_month.items()},
            top_entities=sorted_entities,
        )

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
        trace_id: str | None = None,
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
            "trace_id": trace_id,
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
        trace_id: str | None = None,
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
            "trace_id": trace_id,
            "created_at": now,
        }
        with self._engine.begin() as conn:
            conn.execute(insert(ai_runs_table).values(**data))
        return AiRun(**{**data, "input_payload": input_payload, "output_payload": None})

    def _execute_select(
        self, query, limit: int | None = None
    ) -> list[AiRun]:
        """Execute a select query and return AiRun objects."""
        if limit is not None:
            query = query.limit(limit)
        with self._engine.connect() as conn:
            rows = conn.execute(query).mappings()
            return [_row_to_run(dict(row)) for row in rows]

    def list_latest(self, limit: int = 50) -> list[AiRun]:
        return self._execute_select(
            select(ai_runs_table).order_by(ai_runs_table.c.created_at.desc()),
            limit=limit,
        )

    def get_stats(self) -> dict[str, Any]:
        """Compute aggregate stats via SQL aggregation."""
        from sqlalchemy import func as sa_func

        with self._engine.connect() as conn:
            total = conn.execute(
                select(sa_func.count()).select_from(ai_runs_table)
            ).scalar() or 0

            completed = conn.execute(
                select(sa_func.count()).select_from(ai_runs_table).where(
                    ai_runs_table.c.status == "completed"
                )
            ).scalar() or 0

            avg_latency = conn.execute(
                select(sa_func.avg(ai_runs_table.c.latency_ms)).select_from(
                    ai_runs_table
                ).where(ai_runs_table.c.status == "completed")
            ).scalar() or 0.0

            avg_tokens = conn.execute(
                select(sa_func.avg(ai_runs_table.c.total_tokens)).select_from(
                    ai_runs_table
                ).where(ai_runs_table.c.status == "completed")
            ).scalar() or 0.0

            total_tokens = conn.execute(
                select(sa_func.sum(ai_runs_table.c.total_tokens)).select_from(
                    ai_runs_table
                ).where(ai_runs_table.c.status == "completed")
            ).scalar() or 0

            # Per-stage stats
            stage_rows = conn.execute(
                select(
                    ai_runs_table.c.prompt_name,
                    sa_func.count().label("count"),
                    sa_func.avg(ai_runs_table.c.latency_ms).label("avg_latency"),
                    sa_func.avg(ai_runs_table.c.total_tokens).label("avg_tokens"),
                    sa_func.sum(ai_runs_table.c.total_tokens).label("total_tokens"),
                )
                .where(ai_runs_table.c.status == "completed")
                .group_by(ai_runs_table.c.prompt_name)
                .order_by(ai_runs_table.c.prompt_name)
            ).mappings().all()

            stage_stats: dict[str, dict[str, Any]] = {}
            for row in stage_rows:
                stage_stats[row["prompt_name"]] = {
                    "count": row["count"],
                    "avg_latency_ms": round(row["avg_latency"] or 0, 1),
                    "avg_total_tokens": round(row["avg_tokens"] or 0, 1),
                    "total_tokens": row["total_tokens"] or 0,
                }

        return {
            "total_runs": total,
            "completed": completed,
            "failed": total - completed,
            "success_rate": round(completed / total * 100, 1) if total else 0.0,
            "avg_latency_ms": round(avg_latency, 1),
            "avg_total_tokens": round(avg_tokens, 1),
            "total_tokens": total_tokens,
            "stages": stage_stats,
        }

    def get_cost_stats(self) -> CostStats:
        """Return cost breakdown from DB."""
        with self._engine.connect() as conn:
            rows = conn.execute(
                select(
                    ai_runs_table.c.model,
                    ai_runs_table.c.prompt_name,
                    ai_runs_table.c.prompt_tokens,
                    ai_runs_table.c.completion_tokens,
                    ai_runs_table.c.entity_type,
                    ai_runs_table.c.entity_id,
                    ai_runs_table.c.created_at,
                )
                .where(ai_runs_table.c.status == "completed")
            ).mappings().all()

        if not rows:
            return CostStats(
                total_cost=0.0,
                avg_cost_per_run=0.0,
                cost_by_model={},
                cost_by_stage={},
                cost_by_month={},
                top_entities=[],
            )

        total_cost = 0.0
        count = 0
        cost_by_model: dict[str, float] = {}
        cost_by_stage: dict[str, float] = {}
        cost_by_month: dict[str, float] = {}
        entity_costs: dict[str, float] = {}

        for row in rows:
            cost = compute_cost(
                row["prompt_tokens"], row["completion_tokens"], row["model"]
            )
            total_cost += cost
            count += 1

            model_key = row["model"] or "unknown"
            cost_by_model[model_key] = cost_by_model.get(model_key, 0.0) + cost
            cost_by_stage[row["prompt_name"]] = cost_by_stage.get(row["prompt_name"], 0.0) + cost

            if row["created_at"]:
                month_key = row["created_at"].strftime("%Y-%m")
                cost_by_month[month_key] = cost_by_month.get(month_key, 0.0) + cost

            entity_key = f"{row['entity_type']}:{row['entity_id']}"
            entity_costs[entity_key] = entity_costs.get(entity_key, 0.0) + cost

        sorted_entities = sorted(
            [{"entity": k, "cost": round(v, 4)} for k, v in entity_costs.items()],
            key=lambda x: x["cost"],
            reverse=True,
        )[:10]

        return CostStats(
            total_cost=round(total_cost, 4),
            avg_cost_per_run=round(total_cost / count, 4) if count else 0.0,
            cost_by_model={k: round(v, 4) for k, v in cost_by_model.items()},
            cost_by_stage={k: round(v, 4) for k, v in cost_by_stage.items()},
            cost_by_month={k: round(v, 4) for k, v in cost_by_month.items()},
            top_entities=sorted_entities,
        )

    def list_for_entity(self, entity_type: str, entity_id: str) -> list[AiRun]:
        return self._execute_select(
            select(ai_runs_table)
            .where(
                ai_runs_table.c.entity_type == entity_type,
                ai_runs_table.c.entity_id == entity_id,
            )
            .order_by(ai_runs_table.c.created_at.desc())
        )


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
