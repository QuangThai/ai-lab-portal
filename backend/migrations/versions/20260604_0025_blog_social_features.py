"""Add blog social features tables (reactions, bookmarks, comments).

Revision ID: 20260604_0025
Revises: 20260604_0024
Create Date: 2026-06-04 13:30:00
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260604_0025"
down_revision: str | None = "20260604_0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "blog_reactions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("post_id", sa.String(64), sa.ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("user_email", sa.String(320), nullable=True),
        sa.Column("emoji", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("post_id", "user_id", "emoji", name="uq_blog_reactions_post_user_emoji"),
    )
    op.create_index("ix_blog_reactions_post_id", "blog_reactions", ["post_id"])

    op.create_table(
        "blog_bookmarks",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("post_id", sa.String(64), sa.ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("user_email", sa.String(320), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("post_id", "user_id", name="uq_blog_bookmarks_post_user"),
    )
    op.create_index("ix_blog_bookmarks_user_id", "blog_bookmarks", ["user_id"])
    op.create_index("ix_blog_bookmarks_post_id", "blog_bookmarks", ["post_id"])

    op.create_table(
        "blog_comments",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("post_id", sa.String(64), sa.ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("user_email", sa.String(320), nullable=True),
        sa.Column("user_name", sa.String(160), nullable=True),
        sa.Column("parent_id", sa.String(64), sa.ForeignKey("blog_comments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_blog_comments_post_id", "blog_comments", ["post_id"])
    op.create_index("ix_blog_comments_status", "blog_comments", ["status"])


def downgrade() -> None:
    op.drop_table("blog_comments")
    op.drop_table("blog_bookmarks")
    op.drop_table("blog_reactions")
