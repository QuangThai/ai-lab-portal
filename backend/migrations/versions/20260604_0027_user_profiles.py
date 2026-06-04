"""Add user profiles table.

Revision ID: 20260604_0027
Revises: 20260604_0026
Create Date: 2026-06-04 14:25:00
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260604_0027"
down_revision: str | None = "20260604_0026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_profiles",
        sa.Column("user_id", sa.String(255), sa.ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.String(2048), nullable=True),
        sa.Column("website_url", sa.String(2048), nullable=True),
        sa.Column("github_url", sa.String(2048), nullable=True),
        sa.Column("linkedin_url", sa.String(2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("user_profiles")
