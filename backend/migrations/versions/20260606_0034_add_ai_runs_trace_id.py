"""Add trace_id column to ai_runs table

Revision ID: 0034
Revises: 0033
Create Date: 2026-06-06 18:00:00.000000

"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260606_0034"
down_revision: str | None = "20260606_0033"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("ai_runs", sa.Column("trace_id", sa.String(80), nullable=True))


def downgrade() -> None:
    op.drop_column("ai_runs", "trace_id")
