"""add showcases read model

Revision ID: 20260602_0005
Revises: 20260602_0004
Create Date: 2026-06-02
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260602_0005"
down_revision: str | None = "20260602_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "showcases",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("hero_summary", sa.Text(), nullable=False),
        sa.Column("industry", sa.String(length=120), nullable=True),
        sa.Column("use_case", sa.String(length=240), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_showcases_slug"),
    )
    op.create_index("ix_showcases_status_published_at", "showcases", ["status", "published_at"])


def downgrade() -> None:
    op.drop_index("ix_showcases_status_published_at", table_name="showcases")
    op.drop_table("showcases")
