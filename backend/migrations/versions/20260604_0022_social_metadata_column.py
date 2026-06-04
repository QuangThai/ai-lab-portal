"""add social_metadata column to news_review_items for US-057

Revision ID: 20260604_0022
Revises: 20260604_0021
Create Date: 2026-06-04
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260604_0022"
down_revision: str | None = "20260604_0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "news_review_items",
        sa.Column("social_metadata", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("news_review_items", "social_metadata")
