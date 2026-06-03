"""add publish fields to news_review_items

Revision ID: 20260603_0018
Revises: 20260603_0017
Create Date: 2026-06-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260603_0018"
down_revision: str | None = "20260603_0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("news_review_items", sa.Column("slug", sa.String(length=160), nullable=True))
    op.add_column(
        "news_review_items",
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_news_review_items_slug", "news_review_items", ["slug"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_news_review_items_slug", table_name="news_review_items")
    op.drop_column("news_review_items", "published_at")
    op.drop_column("news_review_items", "slug")
