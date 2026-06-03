"""add news_submitted_links for user link submission

Revision ID: 20260603_0019
Revises: 20260603_0018
Create Date: 2026-06-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260603_0019"
down_revision: str | None = "20260603_0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "news_submitted_links",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("url_normalized", sa.String(length=1024), nullable=False),
        sa.Column("submitter_name", sa.String(length=160), nullable=True),
        sa.Column("submitter_email", sa.String(length=320), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("suggested_category", sa.String(length=160), nullable=True),
        sa.Column("rate_limit_key", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("processing_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("url_normalized", name="uq_news_submitted_links_url_normalized"),
    )
    op.create_index("ix_news_submitted_links_status", "news_submitted_links", ["status"])
    op.create_index("ix_news_submitted_links_rate_key", "news_submitted_links", ["rate_limit_key"])


def downgrade() -> None:
    op.drop_index("ix_news_submitted_links_rate_key", table_name="news_submitted_links")
    op.drop_index("ix_news_submitted_links_status", table_name="news_submitted_links")
    op.drop_table("news_submitted_links")
