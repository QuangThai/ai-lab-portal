"""add blog_ideas table for AI Blog Agent

Revision ID: 20260602_0006
Revises: 20260602_0005
Create Date: 2026-06-02
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260602_0006"
down_revision: str | None = "20260602_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "blog_ideas",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("angle", sa.String(length=160), nullable=False),
        sa.Column("target_reader", sa.String(length=160), nullable=False),
        sa.Column("article_goal", sa.Text(), nullable=False),
        sa.Column("positioning_notes", sa.Text(), nullable=True),
        sa.Column(
            "source",
            sa.String(length=32),
            nullable=False,
            server_default="manual",
        ),
        sa.Column("source_project_context", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("reviewed_by", sa.String(length=128), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_blog_ideas_status", "blog_ideas", ["status"])
    op.create_index(
        "ix_blog_ideas_created_at", "blog_ideas", ["created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_blog_ideas_created_at", table_name="blog_ideas")
    op.drop_index("ix_blog_ideas_status", table_name="blog_ideas")
    op.drop_table("blog_ideas")
