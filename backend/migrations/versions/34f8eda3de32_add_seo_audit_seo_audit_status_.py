"""add seo_audit seo_audit_status scheduled_at to blog_ideas

Revision ID: 34f8eda3de32
Revises: 20260606_0034
Create Date: 2026-06-08 10:34:12.211611
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '34f8eda3de32'
down_revision: str | None = '20260606_0034'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("blog_ideas", sa.Column("seo_audit", sa.Text(), nullable=True))
    op.add_column("blog_ideas", sa.Column("seo_audit_status", sa.String(32), nullable=True))
    op.add_column("blog_ideas", sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("blog_ideas", "scheduled_at")
    op.drop_column("blog_ideas", "seo_audit_status")
    op.drop_column("blog_ideas", "seo_audit")
