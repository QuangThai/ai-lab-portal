"""add technical review fields to blog_ideas for Technical Reviewer workflow

Revision ID: 20260602_0009
Revises: 20260602_0008
Create Date: 2026-06-02
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260602_0009"
down_revision: str | None = "20260602_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "blog_ideas",
        sa.Column("technical_review", sa.Text(), nullable=True),
    )
    op.add_column(
        "blog_ideas",
        sa.Column(
            "technical_review_status",
            sa.String(length=32),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_blog_ideas_review_status",
        "blog_ideas",
        ["technical_review_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_blog_ideas_review_status", table_name="blog_ideas")
    op.drop_column("blog_ideas", "technical_review_status")
    op.drop_column("blog_ideas", "technical_review")
