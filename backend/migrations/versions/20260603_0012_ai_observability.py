"""ai_runs, blog_generation_jobs, and blog_claims tables

Revision ID: 20260603_0012
Revises: 20260603_0011
Create Date: 2026-06-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260603_0012"
down_revision: str | None = "20260603_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_runs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("prompt_name", sa.String(length=80), nullable=False),
        sa.Column("prompt_version", sa.String(length=32), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("input_payload", sa.Text(), nullable=False),
        sa.Column("output_payload", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ai_runs_entity", "ai_runs", ["entity_type", "entity_id"])
    op.create_index("ix_ai_runs_prompt", "ai_runs", ["prompt_name", "created_at"])

    op.create_table(
        "blog_generation_jobs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("blog_idea_id", sa.String(length=64), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("celery_task_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_blog_generation_jobs_idea",
        "blog_generation_jobs",
        ["blog_idea_id", "created_at"],
    )
    op.create_index(
        "ix_blog_generation_jobs_celery_task_id",
        "blog_generation_jobs",
        ["celery_task_id"],
        unique=True,
    )

    op.create_table(
        "blog_claims",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("blog_idea_id", sa.String(length=64), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("evidence_source_type", sa.String(length=32), nullable=True),
        sa.Column("evidence_reference", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_blog_claims_idea", "blog_claims", ["blog_idea_id"])


def downgrade() -> None:
    op.drop_index("ix_blog_claims_idea", table_name="blog_claims")
    op.drop_table("blog_claims")
    op.drop_index("ix_blog_generation_jobs_celery_task_id", table_name="blog_generation_jobs")
    op.drop_index("ix_blog_generation_jobs_idea", table_name="blog_generation_jobs")
    op.drop_table("blog_generation_jobs")
    op.drop_index("ix_ai_runs_prompt", table_name="ai_runs")
    op.drop_index("ix_ai_runs_entity", table_name="ai_runs")
    op.drop_table("ai_runs")
