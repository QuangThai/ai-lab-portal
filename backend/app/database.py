from sqlalchemy import Column, DateTime, Index, MetaData, String, Table, Text, create_engine
from sqlalchemy.engine import Engine

from backend.app.settings import Settings

metadata = MetaData()


def create_database_engine(settings: Settings) -> Engine:
    return create_engine(str(settings.database_url), pool_pre_ping=True)

blog_posts = Table(
    "blog_posts",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("slug", String(160), nullable=False, unique=True),
    Column("title", String(240), nullable=False),
    Column("excerpt", Text, nullable=False),
    Column("author_name", String(120), nullable=False),
    Column("status", String(32), nullable=False),
    Column("published_at", DateTime(timezone=True), nullable=True),
    Column("content_markdown", Text, nullable=False),
)

showcases = Table(
    "showcases",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("slug", String(160), nullable=False, unique=True),
    Column("title", String(240), nullable=False),
    Column("hero_summary", Text, nullable=False),
    Column("industry", String(120), nullable=True),
    Column("use_case", String(240), nullable=True),
    Column("status", String(32), nullable=False),
    Column("published_at", DateTime(timezone=True), nullable=True),
    Column("content_markdown", Text, nullable=False),
    Index("ix_showcases_status_published_at", "status", "published_at"),
)

audit_events = Table(
    "audit_events",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("actor_user_id", String(128), nullable=False),
    Column("actor_email", String(320), nullable=False),
    Column("action", String(80), nullable=False),
    Column("entity_type", String(80), nullable=False),
    Column("entity_id", String(128), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_audit_events_entity", "entity_type", "entity_id"),
    Index("ix_audit_events_actor", "actor_user_id"),
)

blog_ideas = Table(
    "blog_ideas",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("title", String(240), nullable=False),
    Column("angle", String(160), nullable=False),
    Column("target_reader", String(160), nullable=False),
    Column("article_goal", Text, nullable=False),
    Column("positioning_notes", Text, nullable=True),
    Column("source", String(32), nullable=False),
    Column("source_project_context", Text, nullable=True),
    Column("status", String(32), nullable=False),
    Column("reviewed_by", String(128), nullable=True),
    Column("reviewed_at", DateTime(timezone=True), nullable=True),
    Column("feedback", Text, nullable=True),
    Column("outline_sections", Text, nullable=True),
    Column("outline_status", String(32), nullable=True),
    Column("draft_markdown", Text, nullable=True),
    Column("draft_status", String(32), nullable=True),
    Column("technical_review", Text, nullable=True),
    Column("technical_review_status", String(32), nullable=True),
    Column("marketing_metadata", Text, nullable=True),
    Column("marketing_status", String(32), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_blog_ideas_status", "status"),
    Index("ix_blog_ideas_created_at", "created_at"),
    Index("ix_blog_ideas_outline_status", "outline_status"),
    Index("ix_blog_ideas_draft_status", "draft_status"),
    Index("ix_blog_ideas_review_status", "technical_review_status"),
    Index("ix_blog_ideas_marketing_status", "marketing_status"),
)
