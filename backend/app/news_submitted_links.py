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
from urllib.parse import urlparse

from backend.app.database import news_submitted_links as submitted_table
from backend.app.news_crawl import NewsRawItemRepository, ParsedFeedItem, UnsafeUrlError, content_hash_for_item, validate_fetch_url
from backend.app.news_dedup import canonicalize_url
from backend.app.news_extraction import ArticleExtractor, ExtractedArticleRepository
from backend.app.news_scoring import NewsReviewRepository
from backend.app.news_sources import NewsSourceRepository
from backend.app.settings import Settings

SubmittedLinkStatus = Literal["submitted", "processing", "duplicate", "failed", "in_review"]
DEFAULT_RATE_LIMIT_PER_HOUR = 5
USER_SUBMISSION_SOURCE_ID = "newssrc_user_submissions"


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
    raw_item_id: str | None = None
    review_item_id: str | None = None
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
        raw_item_id: str | None = None,
        review_item_id: str | None = None,
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
        raw_item_id: str | None = None,
        review_item_id: str | None = None,
    ) -> SubmittedLinkSummary | None:
        row = self._rows.get(submission_id)
        if row is None:
            return None
        update_fields: dict[str, object] = {
            "status": status,
            "processing_error": processing_error,
            "updated_at": datetime.now(UTC),
        }
        if raw_item_id is not None:
            update_fields["raw_item_id"] = raw_item_id
        if review_item_id is not None:
            update_fields["review_item_id"] = review_item_id
        updated = row.model_copy(update=update_fields)
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
            "raw_item_id": None,
            "review_item_id": None,
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
        raw_item_id: str | None = None,
        review_item_id: str | None = None,
    ) -> SubmittedLinkSummary | None:
        now = datetime.now(UTC)
        values: dict[str, object] = {
            "status": status,
            "processing_error": processing_error,
            "updated_at": now,
        }
        if raw_item_id is not None:
            values["raw_item_id"] = raw_item_id
        if review_item_id is not None:
            values["review_item_id"] = review_item_id
        with self._engine.begin() as conn:
            conn.execute(
                update(submitted_table)
                .where(submitted_table.c.id == submission_id)
                .values(**values)
            )
        return self.get_by_id(submission_id)


def _submission_title(submission: SubmittedLinkSummary) -> str:
    note = (submission.note or "").strip()
    if note:
        return note[:512]
    parsed = urlparse(submission.url)
    slug = parsed.path.rstrip("/").split("/")[-1] or parsed.hostname or "link"
    return f"Submitted: {slug}"[:512]


def ensure_user_submission_source(sources: NewsSourceRepository):
    source = sources.get_by_id(USER_SUBMISSION_SOURCE_ID)
    if source is None:
        raise ValueError(f"Missing news source: {USER_SUBMISSION_SOURCE_ID}")
    return source


def materialize_submission_raw_item(
    submission: SubmittedLinkSummary,
    *,
    source_id: str,
    raw_items: NewsRawItemRepository,
):
    item = ParsedFeedItem(
        external_id=submission.id,
        title=_submission_title(submission),
        link_url=submission.url,
        published_at=None,
        raw_payload={
            "submission_id": submission.id,
            "suggested_category": submission.suggested_category or "",
            "submitter_email": submission.submitter_email or "",
        },
    )
    fetched_at = datetime.now(UTC)
    raw_items.upsert_item(
        source_id=source_id,
        item=item,
        content_hash=content_hash_for_item(item),
        fetched_at=fetched_at,
    )
    for row in raw_items.list_for_source(source_id):
        if row.external_id == submission.id:
            return row
    raise RuntimeError(f"Failed to materialize raw item for submission {submission.id}")


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
    raw_items: NewsRawItemRepository,
    sources: NewsSourceRepository,
    review: NewsReviewRepository,
    extractor: ArticleExtractor,
) -> SubmittedLinkSummary:
    row = repository.get_by_id(submission_id)
    if row is None:
        raise ValueError(f"Submission not found: {submission_id}")

    if row.raw_item_id and row.status in {"in_review", "submitted", "duplicate"}:
        return row

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

    source = ensure_user_submission_source(sources)
    raw_item = materialize_submission_raw_item(row, source_id=source.id, raw_items=raw_items)

    from backend.app.news_extraction import run_extract_raw_item

    extract_result = run_extract_raw_item(
        raw_item.id,
        raw_items=raw_items,
        extracted=extracted,
        extractor=extractor,
        sources=sources,
        review=review,
    )
    if extract_result.status != "success" or not extract_result.extraction_id:
        updated = repository.set_status(
            submission_id,
            status="failed",
            raw_item_id=raw_item.id,
            processing_error=extract_result.error or "Extraction failed",
        )
        assert updated is not None
        return updated

    article = extracted.get_by_id(extract_result.extraction_id)
    if article is not None and article.duplicate_status != "unique":
        updated = repository.set_status(
            submission_id,
            status="duplicate",
            raw_item_id=raw_item.id,
            processing_error=f"Duplicate article: {article.duplicate_status}",
        )
        assert updated is not None
        return updated

    review_item = review.get_by_extracted_article_id(extract_result.extraction_id)
    final_status: SubmittedLinkStatus = "in_review" if review_item and review_item.review_status == "candidate" else "submitted"
    updated = repository.set_status(
        submission_id,
        status=final_status,
        raw_item_id=raw_item.id,
        review_item_id=review_item.id if review_item else None,
    )
    assert updated is not None
    return updated


def create_submitted_link_routes(
    repository: SubmittedLinkRepository,
    settings: Settings,
    *,
    extracted_repository: ExtractedArticleRepository | None = None,
    raw_items_repository: NewsRawItemRepository | None = None,
    sources_repository: NewsSourceRepository | None = None,
    review_repository: NewsReviewRepository | None = None,
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
        from backend.app.task_support import (
            article_extractor,
            extracted_article_repository,
            news_raw_item_repository,
            news_review_repository,
            news_source_repository,
        )

        if enqueue_process is not None:
            return ProcessQueuedResponse(task_id=enqueue_process(submission_id))

        return run_process_submitted_link(
            submission_id,
            repository=repository,
            extracted=extracted_repository or extracted_article_repository(settings),
            raw_items=raw_items_repository or news_raw_item_repository(settings),
            sources=sources_repository or news_source_repository(settings),
            review=review_repository or news_review_repository(settings),
            extractor=article_extractor(settings),
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
