"""add image_url column to showcases for featured images

Revision ID: 20260604_0024
Revises: 20260604_0023
Create Date: 2026-06-04
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260604_0024"
down_revision: str | None = "20260604_0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "showcases",
        sa.Column("image_url", sa.String(length=2048), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("showcases", "image_url")
