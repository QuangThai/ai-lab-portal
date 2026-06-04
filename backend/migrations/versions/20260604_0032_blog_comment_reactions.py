"""Add blog_comment_reactions table

Revision ID: 0032
Revises: 0031
Create Date: 2026-06-04 21:30:00.000000

"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260604_0032"
down_revision: str | None = "20260604_0031"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "blog_comment_reactions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("comment_id", sa.String(64), sa.ForeignKey("blog_comments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("user_email", sa.String(320), nullable=True),
        sa.Column("emoji", sa.String(32), nullable=False, server_default=sa.text("'❤'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("comment_id", "user_id", name="uq_blog_cmt_react_comment_user"),
    )
    op.create_index("ix_blog_comment_reactions_comment_id", "blog_comment_reactions", ["comment_id"])


def downgrade() -> None:
    op.drop_table("blog_comment_reactions")
