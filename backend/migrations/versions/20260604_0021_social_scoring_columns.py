"""add social scoring columns to news_review_items for US-056

Revision ID: 20260604_0021
Revises: 20260603_0020
Create Date: 2026-06-04
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260604_0021"
down_revision: str | None = "20260603_0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "news_review_items",
        sa.Column("author_credibility_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "news_review_items",
        sa.Column("social_engagement_score", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("news_review_items", "social_engagement_score")
    op.drop_column("news_review_items", "author_credibility_score")
