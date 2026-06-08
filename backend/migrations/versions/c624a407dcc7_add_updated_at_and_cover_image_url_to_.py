"""add updated_at and cover_image_url to blog_posts

Revision ID: c624a407dcc7
Revises: 34f8eda3de32
Create Date: 2026-06-08 12:09:05.912737
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'c624a407dcc7'
down_revision: str | None = '34f8eda3de32'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("blog_posts", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("blog_posts", sa.Column("cover_image_url", sa.String(2048), nullable=True))


def downgrade() -> None:
    op.drop_column("blog_posts", "cover_image_url")
    op.drop_column("blog_posts", "updated_at")
