"""link submitted links to raw items and review queue

Revision ID: 20260603_0020
Revises: 20260603_0019
Create Date: 2026-06-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260603_0020"
down_revision: str | None = "20260603_0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "news_submitted_links",
        sa.Column("raw_item_id", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "news_submitted_links",
        sa.Column("review_item_id", sa.String(length=64), nullable=True),
    )
    op.create_foreign_key(
        "fk_news_submitted_raw_item",
        "news_submitted_links",
        "news_raw_items",
        ["raw_item_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_news_submitted_review_item",
        "news_submitted_links",
        "news_review_items",
        ["review_item_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_news_submitted_review_item", "news_submitted_links", type_="foreignkey")
    op.drop_constraint("fk_news_submitted_raw_item", "news_submitted_links", type_="foreignkey")
    op.drop_column("news_submitted_links", "review_item_id")
    op.drop_column("news_submitted_links", "raw_item_id")
