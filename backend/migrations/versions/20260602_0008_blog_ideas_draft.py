"""add draft fields to blog_ideas for Draft Writer workflow

Revision ID: 20260602_0008
Revises: 20260602_0007
Create Date: 2026-06-02
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260602_0008"
down_revision: str | None = "20260602_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "blog_ideas",
        sa.Column("draft_markdown", sa.Text(), nullable=True),
    )
    op.add_column(
        "blog_ideas",
        sa.Column(
            "draft_status",
            sa.String(length=32),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_blog_ideas_draft_status",
        "blog_ideas",
        ["draft_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_blog_ideas_draft_status", table_name="blog_ideas")
    op.drop_column("blog_ideas", "draft_status")
    op.drop_column("blog_ideas", "draft_markdown")
