"""Add contact_messages table.

Revision ID: 20260604_0029
Revises: 20260604_0028
Create Date: 2026-06-04 21:00:00
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260604_0029"
down_revision: str | None = "20260604_0028"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "contact_messages",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
