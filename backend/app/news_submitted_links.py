"""User-submitted AI news links (MVP 4 / US-044)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from sqlalchemy import Engine, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    AdminIdentity,
    require_admin_identity_with_settings,
)
from backend.app.database import news_submitted_links as submitted_table
from backend.app.news_crawl import UnsafeUrlError, validate_fetch_url
from backend.app.news_dedup import canonicalize_url
from backend.app.news_extraction import ExtractedArticleRepository
from backend.app.settings import Settings

SubmittedLinkStatus = Literal["submitted", "processing", "duplicate", "failed"]
DEFAULT_RATE_LIMIT_PER_HOUR = 5


class SubmittedLinkCreate(BaseModel):
    url: HttpUrl
    submitter_name: str | None = Field(default=None, max_length=160)
    submitter_email: EmailStr | None = None
    note: str | None = Field(default=None, max_length=2000)
    suggested_category: str | None = Field(default=None, max_length=160)


class SubmittedLinkSummary(BaseModel):
    id: str
    url: str
    url_normalized: str
    submitter_name: str | None = None
    submitter_email: str | None = None
    note: str | None = None
    suggested_category: str | None = None
    rate_limit_key: str
    status: SubmittedLinkStatus
    processing_error: str | None = None
    created_at: datetime
    updated_at: datetime


class SubmittedLinkResponse(BaseModel):
    id: str
    status: SubmittedLinkStatus
    message: str
    duplicate: bool = False


class ProcessQueuedResponse(BaseModel):
    status: str = "queued"
    task_id: str


def build_rate_limit_key(*, client_host: str | None, submitter_email: str | None) -> str:
    if submitter_email:
        return f"email:{submitter_email.lower()}"
    return f"ip:{client_host or 'unknown'}"


class SubmittedLinkRepository(ABC):
    @abstractmethod
    def get_by_id(self, submission_id: str) -> SubmittedLinkSummary | None:
        ...

    @abstractmethod
    def get_by_url_normalized(self, url_normalized: str) -> SubmittedLinkSummary | None:
        ...

    @abstractmethod
    def list_all(self, *, limit: int = 100) -> list[SubmittedLinkSummary]:
        ...

    @abstractmethod
    def count_recent_for_rate_key(self, rate_limit_key_value: str, *, since: datetime) -> int:
        ...

    @abstractmethod
    def create(
        self,
        *,
        url: str,
        url_normalized: str,
        rate_limit_key_value: str,
        submitter_name: str | None,
        submitter_email: str | None,
        note: str | None,
        suggested_category: str | None,
    ) -> SubmittedLinkSummary:
        ...

    @abstractmethod
    def set_status(
        self,
        submission_id: str,
        *,
        status: SubmittedLinkStatus,
        processing_error: str | None = None,
    ) -> SubmittedLinkSummary | None:
        ...


class InMemorySubmittedLinkRepository(SubmittedLinkRepository):
    def __init__(self) -> None:
        self._rows: dict[str, SubmittedLinkSummary] = {}

    def get_by_id(self, submission_id: str) -> SubmittedLinkSummary | None:
        return self._rows.get(submission_id)

    def get_by_url_normalized(self, url_normalized: str) -> SubmittedLinkSummary | None:
        for row in self._rows.values():
            if row.url_normalized == url_normalized:
                return row
        return None

    def list_all(self, *, limit: int = 100) -> list[SubmittedLinkSummary]:
        rows = sorted(self._rows.values(), key=lambda row: row.created_at, reverse=True)
        return rows[:limit]

    def count_recent_for_rate_key(self, rate_limit_key_value: str, *, since: datetime) -> int:
        return sum(
            1
            for row in self._rows.values()
            if row.rate_limit_key == rate_limit_key_value and row.created_at >= since
        )

    def create(
        self,
        *,
        url: str,
        url_normalized: str,
        rate_limit_key_value: str,
        submitter_name: str | None,
        submitter_email: str | None,
        note: str | None,
        suggested_category: str | None,
    ) -> SubmittedLinkSummary:
        now = datetime.now(UTC)
        row = SubmittedLinkSummary(
            id=f"newssub_{uuid4().hex}",
            url=url,
            url_normalized=url_normalized,
            submitter_name=submitter_name,
            submitter_email=submitter_email,
            note=note,
            suggested_category=suggested_category,
            rate_limit_key=rate_limit_key_value,
            status="submitted",
            created_at=now,
            updated_at=now,
        )
        self._rows[row.id] = row
        return row

    def set_status(
        self,
        submission_id: str,
        *,
        status: SubmittedLinkStatus,
        processing_error: str | None = None,
    ) -> SubmittedLinkSummary | None:
        row = self._rows.get(submission_id)
        if row is None:
            return None
        updated = row.model_copy(
            update={
                "status": status,
                "processing_error": processing_error,
                "updated_at": datetime.now(UTC),
            }
        )
        self._rows[submission_id] = updated
        return updated


class PostgresSubmittedLinkRepository(SubmittedLinkRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_by_id(self, submission_id: str) -> SubmittedLinkSummary | None:
        with self._engine.connect() as conn:
            row = (
                conn.execute(select(submitted_table).where(submitted_table.c.id == submission_id))
                .mappings()
                .one_or_none()
            )
            if row is None:
                return None
            return SubmittedLinkSummary(**dict(row))

    def get_by_url_normalized(self, url_normalized: str) -> SubmittedLinkSummary | None:
        with self._engine.connect() as conn:
            row = (
                conn.execute(
                    select(submitted_table).where(submitted_table.c.url_normalized == url_normalized)
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                return None
            return SubmittedLinkSummary(**dict(row))

    def list_all(self, *, limit: int = 100) -> list[SubmittedLinkSummary]:
        stmt = select(submitted_table).order_by(submitted_table.c.created_at.desc()).limit(limit)
        with self._engine.connect() as conn:
            rows = conn.execute(stmt).mappings().all()
            return [SubmittedLinkSummary(**dict(row)) for row in rows]

    def count_recent_for_rate_key(self, rate_limit_key_value: str, *, since: datetime) -> int:
        with self._engine.connect() as conn:
            count = conn.execute(
                select(func.count())
                .select_from(submitted_table)
                .where(
                    submitted_table.c.rate_limit_key == rate_limit_key_value,
                    submitted_table.c.created_at >= since,
                )
            ).scalar_one()
            return int(count)

    def create(
        self,
        *,
        url: str,
        url_normalized: str,
        rate_limit_key_value: str,
        submitter_name: str | None,
        submitter_email: str | None,
        note: str | None,
        suggested_category: str | None,
    ) -> SubmittedLinkSummary:
        now = datetime.now(UTC)
        values = {
            "id": f"newssub_{uuid4().hex}",
            "url": url,
            "url_normalized": url_normalized,
            "submitter_name": submitter_name,
            "submitter_email": submitter_email,
            "note": note,
            "suggested_category": suggested_category,
            "rate_limit_key": rate_limit_key_value,
            "status": "submitted",
            "processing_error": None,
            "created_at": now,
            "updated_at": now,
        }
        stmt = pg_insert(submitted_table).values(**values)
        stmt = stmt.on_conflict_do_nothing(constraint="uq_news_submitted_links_url_normalized")
        with self._engine.begin() as conn:
            conn.execute(stmt)
        row = self.get_by_url_normalized(url_normalized)
        assert row is not None
        return row

    def set_status(
        self,
        submission_id: str,
        *,
        status: SubmittedLinkStatus,
        processing_error: str | None = None,
    ) -> SubmittedLinkSummary | None:
        now = datetime.now(UTC)
        with self._engine.begin() as conn:
            conn.execute(
                update(submitted_table)
                .where(submitted_table.c.id == submission_id)
                .values(status=status, processing_error=processing_error, updated_at=now)
            )
        return self.get_by_id(submission_id)


def run_submit_link(
    payload: SubmittedLinkCreate,
    *,
    repository: SubmittedLinkRepository,
    rate_limit_key_value: str,
    rate_limit_per_hour: int = DEFAULT_RATE_LIMIT_PER_HOUR,
) -> SubmittedLinkResponse:
    url = str(payload.url)
    try:
        validate_fetch_url(url)
        normalized = canonicalize_url(url)
    except (UnsafeUrlError, ValueError) as exc:
        raise ValueError(str(exc)) from exc

    existing = repository.get_by_url_normalized(normalized)
    if existing is not None:
        return SubmittedLinkResponse(
            id=existing.id,
            status=existing.status,
            message="This URL was already submitted.",
            duplicate=True,
        )

    since = datetime.now(UTC) - timedelta(hours=1)
    if repository.count_recent_for_rate_key(rate_limit_key_value, since=since) >= rate_limit_per_hour:
        raise RuntimeError("Rate limit exceeded. Try again later.")

    row = repository.create(
        url=url,
        url_normalized=normalized,
        rate_limit_key_value=rate_limit_key_value,
        submitter_name=payload.submitter_name,
        submitter_email=str(payload.submitter_email) if payload.submitter_email else None,
        note=payload.note,
        suggested_category=payload.suggested_category,
    )
    return SubmittedLinkResponse(
        id=row.id,
        status=row.status,
        message="Link submitted for review.",
        duplicate=False,
    )


def run_process_submitted_link(
    submission_id: str,
    *,
    repository: SubmittedLinkRepository,
    extracted: ExtractedArticleRepository,
) -> SubmittedLinkSummary:
    row = repository.get_by_id(submission_id)
    if row is None:
        raise ValueError(f"Submission not found: {submission_id}")

    repository.set_status(submission_id, status="processing")
    try:
        validate_fetch_url(row.url)
        normalized = canonicalize_url(row.url)
    except (UnsafeUrlError, ValueError) as exc:
        updated = repository.set_status(submission_id, status="failed", processing_error=str(exc))
        assert updated is not None
        return updated

    existing_article = extracted.find_earliest_by_canonical_url(
        normalized, exclude_id="__none__"
    )
    if existing_article is not None:
        updated = repository.set_status(
            submission_id,
            status="duplicate",
            processing_error="URL already exists in extracted articles",
        )
        assert updated is not None
        return updated

    updated = repository.set_status(submission_id, status="submitted")
    assert updated is not None
    return updated


def create_submitted_link_routes(
    repository: SubmittedLinkRepository,
    settings: Settings,
    *,
    extracted_repository: ExtractedArticleRepository | None = None,
    enqueue_process: Callable[[str], str] | None = None,
    rate_limit_per_hour: int = DEFAULT_RATE_LIMIT_PER_HOUR,
) -> APIRouter:
    def require_identity(
        identity_payload: Annotated[str | None, Header(alias=ADMIN_IDENTITY_HEADER)] = None,
        signature: Annotated[str | None, Header(alias=ADMIN_SIGNATURE_HEADER)] = None,
    ) -> AdminIdentity:
        return require_admin_identity_with_settings(settings, identity_payload, signature)

    router = APIRouter(prefix="/admin/news/submitted-links")

    @router.get("")
    async def list_submitted_links(
        limit: int = 100,
        _identity: AdminIdentity = Depends(require_identity),
    ) -> list[SubmittedLinkSummary]:
        return repository.list_all(limit=limit)

    @router.get("/{submission_id}")
    async def get_submitted_link(
        submission_id: str,
        _identity: AdminIdentity = Depends(require_identity),
    ) -> SubmittedLinkSummary:
        row = repository.get_by_id(submission_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Submission not found")
        return row

    @router.post("/{submission_id}/process")
    async def process_submitted_link(
        submission_id: str,
        _identity: AdminIdentity = Depends(require_identity),
    ):
        from backend.app.task_support import extracted_article_repository

        if enqueue_process is not None:
            return ProcessQueuedResponse(task_id=enqueue_process(submission_id))

        return run_process_submitted_link(
            submission_id,
            repository=repository,
            extracted=extracted_repository or extracted_article_repository(settings),
        )

    return router


def create_public_submitted_link_route(
    repository: SubmittedLinkRepository,
    *,
    enqueue_process: Callable[[str], str] | None = None,
    rate_limit_per_hour: int = DEFAULT_RATE_LIMIT_PER_HOUR,
) -> APIRouter:
    router = APIRouter()

    @router.post("/public/submitted-links")
    async def submit_link(payload: SubmittedLinkCreate, request: Request) -> SubmittedLinkResponse:
        client_host = request.client.host if request.client else None
        key = build_rate_limit_key(
            client_host=client_host,
            submitter_email=str(payload.submitter_email) if payload.submitter_email else None,
        )
        try:
            result = run_submit_link(
                payload,
                repository=repository,
                rate_limit_key_value=key,
                rate_limit_per_hour=rate_limit_per_hour,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=429, detail=str(exc)) from exc

        if enqueue_process is not None and not result.duplicate:
            enqueue_process(result.id)

        return result

    return router
