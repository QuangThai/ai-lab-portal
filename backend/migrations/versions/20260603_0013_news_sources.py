"""add news_sources table for MVP 3 AI News

Revision ID: 20260603_0013
Revises: 20260603_0012
Create Date: 2026-06-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260603_0013"
down_revision: str | None = "20260603_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "news_sources",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("url_or_identifier", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(length=16), nullable=False, server_default="medium"),
        sa.Column("crawl_frequency_minutes", sa.Integer(), nullable=False, server_default="360"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("credibility_base_score", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("last_crawled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_news_sources_enabled", "news_sources", ["is_enabled"])
    op.create_index("ix_news_sources_type", "news_sources", ["source_type"])


def downgrade() -> None:
    op.drop_index("ix_news_sources_type", table_name="news_sources")
    op.drop_index("ix_news_sources_enabled", table_name="news_sources")
    op.drop_table("news_sources")
