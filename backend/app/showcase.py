from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy import Engine, insert, select, update

from backend.app.database import audit_events, showcases

ShowcaseStatus = Literal["draft", "published"]


class Showcase(BaseModel):
    id: str
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str
    hero_summary: str
    industry: str | None = None
    use_case: str | None = None
    status: ShowcaseStatus
    published_at: datetime | None
    content_markdown: str


class ShowcaseCreate(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(min_length=1, max_length=240)
    hero_summary: str = Field(min_length=1)
    industry: str | None = Field(default=None, max_length=120)
    use_case: str | None = Field(default=None, max_length=240)
    content_markdown: str = Field(min_length=1)


class ShowcaseUpdate(BaseModel):
    slug: str | None = Field(default=None, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str | None = Field(default=None, min_length=1, max_length=240)
    hero_summary: str | None = Field(default=None, min_length=1)
    industry: str | None = Field(default=None, max_length=120)
    use_case: str | None = Field(default=None, max_length=240)
    content_markdown: str | None = Field(default=None, min_length=1)


class ShowcaseSummary(BaseModel):
    slug: str
    title: str
    hero_summary: str
    industry: str | None
    use_case: str | None
    published_at: datetime


class ShowcaseDetail(ShowcaseSummary):
    content_markdown: str


class AdminShowcaseSummary(BaseModel):
    id: str
    slug: str
    title: str
    status: ShowcaseStatus
    published_at: datetime | None


class AdminShowcaseDetail(AdminShowcaseSummary):
    hero_summary: str
    industry: str | None
    use_case: str | None
    content_markdown: str


class AuditEvent(BaseModel):
    id: str
    actor_user_id: str
    actor_email: str
    action: str
    entity_type: str
    entity_id: str
    created_at: datetime


class ShowcaseRepository:
    def __init__(self, items: list[Showcase] | None = None) -> None:
        seed_items = list(DEFAULT_SHOWCASES) if items is None else items
        self.items: dict[str, Showcase] = {item.id: item for item in seed_items}

    def get_by_id(self, showcase_id: str) -> AdminShowcaseDetail | None:
        item = self.items.get(showcase_id)
        if item is None:
            return None
        return _to_admin_detail(item)

    def list_all(self) -> list[AdminShowcaseSummary]:
        items = sorted(self.items.values(), key=lambda item: item.published_at or datetime.min.replace(tzinfo=UTC), reverse=True)
        return [_to_admin_summary(item) for item in items]

    def list_published(self) -> list[ShowcaseSummary]:
        items = [item for item in self.items.values() if item.status == "published" and item.published_at]
        items.sort(key=lambda item: item.published_at or datetime.min.replace(tzinfo=UTC), reverse=True)
        return [_to_public_summary(item) for item in items if item.published_at is not None]

    def get_published_by_slug(self, slug: str) -> ShowcaseDetail | None:
        for item in self.items.values():
            if item.slug == slug and item.status == "published" and item.published_at is not None:
                return _to_public_detail(item)
        return None

    def create(self, request: ShowcaseCreate) -> Showcase:
        item = Showcase(id=f"showcase_{uuid4().hex}", status="draft", published_at=None, **request.model_dump())
        self.items[item.id] = item
        return item

    def update(self, showcase_id: str, request: ShowcaseUpdate) -> Showcase | None:
        item = self.items.get(showcase_id)
        if item is None:
            return None
        updated = item.model_copy(update=request.model_dump(exclude_unset=True))
        self.items[showcase_id] = updated
        return updated

    def publish(self, showcase_id: str) -> Showcase | None:
        item = self.items.get(showcase_id)
        if item is None:
            return None
        published = item.model_copy(update={"status": "published", "published_at": datetime.now(UTC)})
        self.items[showcase_id] = published
        return published

    def unpublish(self, showcase_id: str) -> Showcase | None:
        item = self.items.get(showcase_id)
        if item is None:
            return None
        draft = item.model_copy(update={"status": "draft", "published_at": None})
        self.items[showcase_id] = draft
        return draft

    def record_audit(self, actor_user_id: str, actor_email: str, action: str, entity_id: str) -> AuditEvent:
        return AuditEvent(
            id=f"audit_{uuid4().hex}",
            actor_user_id=actor_user_id,
            actor_email=actor_email,
            action=action,
            entity_type="showcase",
            entity_id=entity_id,
            created_at=datetime.now(UTC),
        )


class PostgresShowcaseRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def seed_defaults_when_empty(self) -> None:
        with self.engine.begin() as connection:
            for item in DEFAULT_SHOWCASES:
                existing = connection.execute(select(showcases.c.id).where(showcases.c.slug == item.slug)).first()
                if existing is None:
                    connection.execute(insert(showcases).values(**item.model_dump()))

    def get_by_id(self, showcase_id: str) -> AdminShowcaseDetail | None:
        self.seed_defaults_when_empty()
        with self.engine.begin() as connection:
            row = connection.execute(select(showcases).where(showcases.c.id == showcase_id)).mappings().first()
            if row is None:
                return None
            return AdminShowcaseDetail.model_validate(dict(row))

    def list_all(self) -> list[AdminShowcaseSummary]:
        self.seed_defaults_when_empty()
        with self.engine.begin() as connection:
            rows = connection.execute(select(showcases).order_by(showcases.c.published_at.desc().nullslast())).mappings()
            return [AdminShowcaseSummary.model_validate(dict(row)) for row in rows]

    def list_published(self) -> list[ShowcaseSummary]:
        self.seed_defaults_when_empty()
        with self.engine.begin() as connection:
            rows = connection.execute(
                select(showcases)
                .where(showcases.c.status == "published", showcases.c.published_at.is_not(None))
                .order_by(showcases.c.published_at.desc())
            ).mappings()
            return [ShowcaseSummary.model_validate(dict(row)) for row in rows]

    def get_published_by_slug(self, slug: str) -> ShowcaseDetail | None:
        self.seed_defaults_when_empty()
        with self.engine.begin() as connection:
            row = connection.execute(
                select(showcases).where(
                    showcases.c.slug == slug,
                    showcases.c.status == "published",
                    showcases.c.published_at.is_not(None),
                )
            ).mappings().first()
            if row is None:
                return None
            return ShowcaseDetail.model_validate(dict(row))

    def create(self, request: ShowcaseCreate) -> Showcase:
        item = Showcase(id=f"showcase_{uuid4().hex}", status="draft", published_at=None, **request.model_dump())
        with self.engine.begin() as connection:
            connection.execute(insert(showcases).values(**item.model_dump()))
        return item

    def update(self, showcase_id: str, request: ShowcaseUpdate) -> Showcase | None:
        update_data = request.model_dump(exclude_unset=True)
        with self.engine.begin() as connection:
            existing = connection.execute(select(showcases).where(showcases.c.id == showcase_id)).mappings().first()
            if existing is None:
                return None
            if update_data:
                connection.execute(update(showcases).where(showcases.c.id == showcase_id).values(**update_data))
            row = connection.execute(select(showcases).where(showcases.c.id == showcase_id)).mappings().one()
        return Showcase.model_validate(dict(row))

    def publish(self, showcase_id: str) -> Showcase | None:
        published_at = datetime.now(UTC)
        with self.engine.begin() as connection:
            result = connection.execute(
                update(showcases)
                .where(showcases.c.id == showcase_id)
                .values(status="published", published_at=published_at)
            )
            if result.rowcount == 0:
                return None
            row = connection.execute(select(showcases).where(showcases.c.id == showcase_id)).mappings().one()
        return Showcase.model_validate(dict(row))

    def unpublish(self, showcase_id: str) -> Showcase | None:
        with self.engine.begin() as connection:
            result = connection.execute(
                update(showcases).where(showcases.c.id == showcase_id).values(status="draft", published_at=None)
            )
            if result.rowcount == 0:
                return None
            row = connection.execute(select(showcases).where(showcases.c.id == showcase_id)).mappings().one()
        return Showcase.model_validate(dict(row))

    def record_audit(self, actor_user_id: str, actor_email: str, action: str, entity_id: str) -> AuditEvent:
        event = AuditEvent(
            id=f"audit_{uuid4().hex}",
            actor_user_id=actor_user_id,
            actor_email=actor_email,
            action=action,
            entity_type="showcase",
            entity_id=entity_id,
            created_at=datetime.now(UTC),
        )
        with self.engine.begin() as connection:
            connection.execute(insert(audit_events).values(**event.model_dump()))
        return event


def _to_admin_summary(item: Showcase) -> AdminShowcaseSummary:
    return AdminShowcaseSummary(
        id=item.id,
        slug=item.slug,
        title=item.title,
        status=item.status,
        published_at=item.published_at,
    )


def _to_admin_detail(item: Showcase) -> AdminShowcaseDetail:
    return AdminShowcaseDetail(
        id=item.id,
        slug=item.slug,
        title=item.title,
        status=item.status,
        published_at=item.published_at,
        hero_summary=item.hero_summary,
        industry=item.industry,
        use_case=item.use_case,
        content_markdown=item.content_markdown,
    )


def _to_public_summary(item: Showcase) -> ShowcaseSummary:
    assert item.published_at is not None
    return ShowcaseSummary(
        slug=item.slug,
        title=item.title,
        hero_summary=item.hero_summary,
        industry=item.industry,
        use_case=item.use_case,
        published_at=item.published_at,
    )


def _to_public_detail(item: Showcase) -> ShowcaseDetail:
    return ShowcaseDetail(**_to_public_summary(item).model_dump(), content_markdown=item.content_markdown)


DEFAULT_SHOWCASES: tuple[Showcase, ...] = (
    Showcase(
        id="showcase_001",
        slug="scopelytics",
        title="Scopelytics",
        hero_summary="An analytics workflow that pairs AI-assisted exploration with human review before client-facing insights ship.",
        industry="Analytics",
        use_case="Client reporting",
        status="published",
        published_at=datetime(2026, 6, 1, 9, 0, tzinfo=UTC),
        content_markdown="""Scopelytics demonstrates how AI Lab packages combine structured data review with editorial control.

The team uses the portal to keep exploratory analysis private until a human approves the narrative that clients should see.""",
    ),
    Showcase(
        id="showcase_002",
        slug="ai-interview-system",
        title="AI Interview System",
        hero_summary="A structured interview assistant with evidence-backed scoring and explicit human sign-off before results are shared.",
        industry="Hiring",
        use_case="Interview operations",
        status="published",
        published_at=datetime(2026, 5, 28, 9, 0, tzinfo=UTC),
        content_markdown="""The AI Interview System showcase highlights a workflow where AI drafts questions and summaries, but reviewers control publication.

This keeps hiring guidance credible while still accelerating preparation and debrief work.""",
    ),
    Showcase(
        id="showcase_003",
        slug="draft-internal-assistant",
        title="Draft Internal Assistant",
        hero_summary="Internal-only draft showcase that must remain unpublished.",
        industry="Operations",
        use_case="Internal tooling",
        status="draft",
        published_at=None,
        content_markdown="Draft only.",
    ),
)
