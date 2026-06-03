"""add outline fields to blog_ideas for AI Blog Agent workflow

Revision ID: 20260602_0007
Revises: 20260602_0006
Create Date: 2026-06-02
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260602_0007"
down_revision: str | None = "20260602_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "blog_ideas",
        sa.Column("outline_sections", sa.Text(), nullable=True),
    )
    op.add_column(
        "blog_ideas",
        sa.Column(
            "outline_status",
            sa.String(length=32),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_blog_ideas_outline_status",
        "blog_ideas",
        ["outline_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_blog_ideas_outline_status", table_name="blog_ideas")
    op.drop_column("blog_ideas", "outline_status")
    op.drop_column("blog_ideas", "outline_sections")
