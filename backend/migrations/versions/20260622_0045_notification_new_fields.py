"""Add preview, group_key, link columns to notifications.

Revision ID: 20260622_0045
Revises: 20260608_0044
Create Date: 2026-06-22 23:55:00
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260622_0045"
down_revision: str | None = "20260608_0044"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column("preview", sa.Text, nullable=True, server_default=""))
    op.add_column("notifications", sa.Column("group_key", sa.String(64), nullable=True, server_default=""))
    op.add_column("notifications", sa.Column("link", sa.String(512), nullable=True, server_default=""))
    op.create_index(
        "ix_notifications_group_key",
        "notifications",
        ["group_key"],
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_group_key", table_name="notifications")
    op.drop_column("notifications", "link")
    op.drop_column("notifications", "group_key")
    op.drop_column("notifications", "preview")
