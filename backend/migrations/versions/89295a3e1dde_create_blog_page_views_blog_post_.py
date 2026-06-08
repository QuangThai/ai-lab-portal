"""create blog_page_views blog_post_revisions blog_series blog_series_posts

Revision ID: 89295a3e1dde
Revises: c624a407dcc7
Create Date: 2026-06-08 12:45:14.006612
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '89295a3e1dde'
down_revision: str | None = 'c624a407dcc7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # blog_page_views
    op.create_table(
        "blog_page_views",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("post_id", sa.String(length=64), nullable=False),
        sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("visitor_id", sa.String(length=64), nullable=True),
        sa.Column("referrer", sa.String(length=512), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("path", sa.String(length=256), nullable=True),
    )
    op.create_index("ix_page_views_post_id", "blog_page_views", ["post_id"])
    op.create_index("ix_page_views_viewed_at", "blog_page_views", ["viewed_at"])

    # blog_post_revisions
    op.create_table(
        "blog_post_revisions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("post_id", sa.String(length=64), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("image_url", sa.String(length=2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=255), nullable=True),
        sa.UniqueConstraint("post_id", "revision_number", name="uq_post_revision"),
    )
    op.create_index("ix_blog_post_revisions_post_id", "blog_post_revisions", ["post_id"])

    # blog_series
    op.create_table(
        "blog_series",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("slug", sa.String(length=160), nullable=False, unique=True),
        sa.Column("cover_image_url", sa.String(length=2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # blog_series_posts
    op.create_table(
        "blog_series_posts",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("series_id", sa.String(length=64), nullable=False),
        sa.Column("post_id", sa.String(length=64), nullable=False),
        sa.Column("part_number", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("series_id", "post_id", name="uq_series_post"),
        sa.UniqueConstraint("series_id", "part_number", name="uq_series_part"),
    )
    op.create_index("ix_series_posts_series", "blog_series_posts", ["series_id"])


def downgrade() -> None:
    op.drop_table("blog_series_posts")
    op.drop_table("blog_series")
    op.drop_table("blog_post_revisions")
    op.drop_table("blog_page_views")
