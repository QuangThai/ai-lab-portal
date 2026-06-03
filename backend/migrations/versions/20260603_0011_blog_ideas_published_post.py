"""add published_blog_post_id to blog_ideas

Revision ID: 20260603_0011
Revises: 20260602_0010
Create Date: 2026-06-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260603_0011"
down_revision: str | None = "20260602_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "blog_ideas",
        sa.Column("published_blog_post_id", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_blog_ideas_published_blog_post_id",
        "blog_ideas",
        ["published_blog_post_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_blog_ideas_published_blog_post_id", table_name="blog_ideas")
    op.drop_column("blog_ideas", "published_blog_post_id")
