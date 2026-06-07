"""Durable tracking for queued Celery blog generation jobs."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy import Engine, insert, select, update

from backend.app.database import blog_generation_jobs as jobs_table

GenerationStage = Literal[
    "idea", "outline", "draft", "technical_review", "marketing", "seo_audit"
]
GenerationJobStatus = Literal["queued", "running", "completed", "failed"]


class GenerationJob(BaseModel):
    id: str
    blog_idea_id: str
    stage: GenerationStage
    celery_task_id: str
    status: GenerationJobStatus
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None


class GenerationJobRepository:
    def __init__(self) -> None:
        self._jobs: dict[str, GenerationJob] = {}
        self._by_celery: dict[str, str] = {}

    def create_queued(
        self,
        *,
        blog_idea_id: str,
        stage: GenerationStage,
        celery_task_id: str,
    ) -> GenerationJob:
        now = datetime.now(UTC)
        job = GenerationJob(
            id=f"genjob_{uuid4().hex}",
            blog_idea_id=blog_idea_id,
            stage=stage,
            celery_task_id=celery_task_id,
            status="queued",
            created_at=now,
            updated_at=now,
        )
        self._jobs[job.id] = job
        self._by_celery[celery_task_id] = job.id
        return job

    def get_by_celery_task_id(self, celery_task_id: str) -> GenerationJob | None:
        job_id = self._by_celery.get(celery_task_id)
        if job_id is None:
            return None
        return self._jobs.get(job_id)

    def mark_running(self, celery_task_id: str) -> GenerationJob | None:
        job = self.get_by_celery_task_id(celery_task_id)
        if job is None:
            return None
        updated = job.model_copy(
            update={"status": "running", "updated_at": datetime.now(UTC)}
        )
        self._jobs[job.id] = updated
        return updated

    def mark_completed(self, celery_task_id: str) -> GenerationJob | None:
        job = self.get_by_celery_task_id(celery_task_id)
        if job is None:
            return None
        now = datetime.now(UTC)
        updated = job.model_copy(
            update={"status": "completed", "updated_at": now, "completed_at": now}
        )
        self._jobs[job.id] = updated
        return updated

    def mark_failed(self, celery_task_id: str, error_message: str) -> GenerationJob | None:
        job = self.get_by_celery_task_id(celery_task_id)
        if job is None:
            return None
        now = datetime.now(UTC)
        updated = job.model_copy(
            update={
                "status": "failed",
                "error_message": error_message[:2000],
                "updated_at": now,
                "completed_at": now,
            }
        )
        self._jobs[job.id] = updated
        return updated


class PostgresGenerationJobRepository(GenerationJobRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_queued(
        self,
        *,
        blog_idea_id: str,
        stage: GenerationStage,
        celery_task_id: str,
    ) -> GenerationJob:
        now = datetime.now(UTC)
        job_id = f"genjob_{uuid4().hex}"
        data = {
            "id": job_id,
            "blog_idea_id": blog_idea_id,
            "stage": stage,
            "celery_task_id": celery_task_id,
            "status": "queued",
            "error_message": None,
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
        }
        with self._engine.begin() as conn:
            conn.execute(insert(jobs_table).values(**data))
        return GenerationJob(**data)

    def get_by_celery_task_id(self, celery_task_id: str) -> GenerationJob | None:
        with self._engine.connect() as conn:
            row = (
                conn.execute(
                    select(jobs_table).where(
                        jobs_table.c.celery_task_id == celery_task_id
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                return None
            return GenerationJob(**dict(row))

    def mark_running(self, celery_task_id: str) -> GenerationJob | None:
        return self._update_status(celery_task_id, "running")

    def mark_completed(self, celery_task_id: str) -> GenerationJob | None:
        now = datetime.now(UTC)
        with self._engine.begin() as conn:
            result = conn.execute(
                update(jobs_table)
                .where(jobs_table.c.celery_task_id == celery_task_id)
                .values(status="completed", updated_at=now, completed_at=now)
            )
            if result.rowcount == 0:
                return None
        return self.get_by_celery_task_id(celery_task_id)

    def mark_failed(self, celery_task_id: str, error_message: str) -> GenerationJob | None:
        now = datetime.now(UTC)
        with self._engine.begin() as conn:
            result = conn.execute(
                update(jobs_table)
                .where(jobs_table.c.celery_task_id == celery_task_id)
                .values(
                    status="failed",
                    error_message=error_message[:2000],
                    updated_at=now,
                    completed_at=now,
                )
            )
            if result.rowcount == 0:
                return None
        return self.get_by_celery_task_id(celery_task_id)

    def _update_status(
        self, celery_task_id: str, status: GenerationJobStatus
    ) -> GenerationJob | None:
        now = datetime.now(UTC)
        with self._engine.begin() as conn:
            result = conn.execute(
                update(jobs_table)
                .where(jobs_table.c.celery_task_id == celery_task_id)
                .values(status=status, updated_at=now)
            )
            if result.rowcount == 0:
                return None
        return self.get_by_celery_task_id(celery_task_id)
