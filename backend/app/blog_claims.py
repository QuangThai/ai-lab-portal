"""Claim extraction and evidence ledger for blog ideas."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from typing import TYPE_CHECKING

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import Engine, delete, insert, select, update

from backend.app.database import blog_claims as claims_table

if TYPE_CHECKING:
    from backend.app.blog_ideas import BlogIdea
from backend.app.llm.schemas import ClaimExtractionResult
from backend.app.llm.service import LLMService

ClaimType = Literal[
    "performance", "quantified", "product_capability", "opinion", "other"
]
ClaimStatus = Literal["pending", "supported", "unsupported", "waived"]

_QUANTIFIED_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:%|percent|x|times|ms|seconds?|minutes?|hours?|days?|users?|customers?|requests?)\b",
    re.IGNORECASE,
)


class BlogClaim(BaseModel):
    id: str
    blog_idea_id: str
    claim_text: str
    claim_type: ClaimType
    status: ClaimStatus
    evidence_source_type: str | None = None
    evidence_reference: str | None = None
    created_at: datetime
    updated_at: datetime


class BlogClaimUpdate(BaseModel):
    status: ClaimStatus | None = None
    evidence_source_type: str | None = None
    evidence_reference: str | None = None


class BlogClaimsRepository:
    def __init__(self) -> None:
        self._claims: dict[str, BlogClaim] = {}

    def list_for_idea(self, blog_idea_id: str) -> list[BlogClaim]:
        items = [c for c in self._claims.values() if c.blog_idea_id == blog_idea_id]
        items.sort(key=lambda c: c.created_at)
        return items

    def replace_for_idea(self, blog_idea_id: str, claims: list[BlogClaim]) -> list[BlogClaim]:
        self._claims = {
            cid: c
            for cid, c in self._claims.items()
            if c.blog_idea_id != blog_idea_id
        }
        for claim in claims:
            self._claims[claim.id] = claim
        return self.list_for_idea(blog_idea_id)

    def get_by_id(self, claim_id: str) -> BlogClaim | None:
        return self._claims.get(claim_id)

    def update(self, claim_id: str, payload: BlogClaimUpdate) -> BlogClaim | None:
        claim = self._claims.get(claim_id)
        if claim is None:
            return None
        data = payload.model_dump(exclude_unset=True)
        if "evidence_reference" in data or "evidence_source_type" in data:
            if data.get("evidence_reference") and data.get("status") is None:
                data["status"] = "supported"
        updated = claim.model_copy(update={**data, "updated_at": datetime.now(UTC)})
        self._claims[claim_id] = updated
        return updated


class PostgresBlogClaimsRepository(BlogClaimsRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_for_idea(self, blog_idea_id: str) -> list[BlogClaim]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                select(claims_table)
                .where(claims_table.c.blog_idea_id == blog_idea_id)
                .order_by(claims_table.c.created_at.asc())
            ).mappings()
            return [BlogClaim(**dict(row)) for row in rows]

    def replace_for_idea(self, blog_idea_id: str, claims: list[BlogClaim]) -> list[BlogClaim]:
        with self._engine.begin() as conn:
            conn.execute(
                delete(claims_table).where(claims_table.c.blog_idea_id == blog_idea_id)
            )
            for claim in claims:
                conn.execute(insert(claims_table).values(**claim.model_dump()))
        return self.list_for_idea(blog_idea_id)

    def get_by_id(self, claim_id: str) -> BlogClaim | None:
        with self._engine.connect() as conn:
            row = (
                conn.execute(select(claims_table).where(claims_table.c.id == claim_id))
                .mappings()
                .one_or_none()
            )
            if row is None:
                return None
            return BlogClaim(**dict(row))

    def update(self, claim_id: str, payload: BlogClaimUpdate) -> BlogClaim | None:
        existing = self.get_by_id(claim_id)
        if existing is None:
            return None
        data = payload.model_dump(exclude_unset=True)
        if data.get("evidence_reference") and data.get("status") is None:
            data["status"] = "supported"
        data["updated_at"] = datetime.now(UTC)
        with self._engine.begin() as conn:
            conn.execute(
                update(claims_table).where(claims_table.c.id == claim_id).values(**data)
            )
        return self.get_by_id(claim_id)


def _initial_status(claim_type: ClaimType, requires_evidence: bool) -> ClaimStatus:
    if requires_evidence or claim_type in ("performance", "quantified"):
        return "pending"
    return "supported"


def claims_from_extraction(
    blog_idea_id: str, result: ClaimExtractionResult
) -> list[BlogClaim]:
    now = datetime.now(UTC)
    claims: list[BlogClaim] = []
    for item in result.claims:
        claim_type: ClaimType = item.claim_type  # type: ignore[assignment]
        status = _initial_status(claim_type, item.requires_evidence)
        claims.append(
            BlogClaim(
                id=f"claim_{uuid4().hex}",
                blog_idea_id=blog_idea_id,
                claim_text=item.claim_text.strip(),
                claim_type=claim_type,
                status=status,
                created_at=now,
                updated_at=now,
            )
        )
    return claims


def extract_claims_with_llm(idea: "BlogIdea", service: LLMService) -> ClaimExtractionResult:
    if not idea.draft_markdown or not idea.draft_markdown.strip():
        raise HTTPException(status_code=400, detail="Claim extraction requires draft markdown")
    result = service.generate(
        "claim_extraction",
        inputs={"draft_markdown": idea.draft_markdown},
        output_schema=ClaimExtractionResult,
    )
    return ClaimExtractionResult.model_validate(result.model_dump())


def validate_claims_ready_for_publish(claims: list[BlogClaim]) -> None:
    blocking = [c for c in claims if c.status in ("pending", "unsupported")]
    if not blocking:
        return
    samples = ", ".join(c.claim_text[:60] for c in blocking[:3])
    raise HTTPException(
        status_code=400,
        detail=(
            f"{len(blocking)} claim(s) need evidence or an explicit waiver before publishing. "
            f"Examples: {samples}"
        ),
    )


def heuristic_claims_from_draft(blog_idea_id: str, draft_markdown: str) -> list[BlogClaim]:
    """Fallback when LLM is unavailable (tests): flag quantified sentences."""
    now = datetime.now(UTC)
    claims: list[BlogClaim] = []
    for line in draft_markdown.splitlines():
        text = line.strip()
        if not text or not _QUANTIFIED_RE.search(text):
            continue
        claims.append(
            BlogClaim(
                id=f"claim_{uuid4().hex}",
                blog_idea_id=blog_idea_id,
                claim_text=text[:500],
                claim_type="quantified",
                status="pending",
                created_at=now,
                updated_at=now,
            )
        )
    return claims
