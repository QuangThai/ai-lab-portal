from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

# Project root relative to this test file
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _migrations_dir() -> str:
    return str(PROJECT_ROOT / "backend/migrations")


def test_alembic_head_includes_user_follows() -> None:
    config = Config(str(PROJECT_ROOT / "backend/alembic.ini"))
    config.set_main_option("script_location", _migrations_dir())
    script = ScriptDirectory.from_config(config)

    assert script.get_current_head() == "89295a3e1dde"
    revisions = {rev.revision for rev in script.walk_revisions()}
    assert "20260602_0002" in revisions
    assert "20260602_0005" in revisions
    assert "20260604_0032" in revisions
    # Newest migrations extending beyond the previously tracked head
    assert "34f8eda3de32" in revisions  # add seo_audit columns
    assert "c624a407dcc7" in revisions  # add updated_at + cover_image_url
    assert "89295a3e1dde" in revisions  # create blog_page_views + blog_post_revisions + blog_series


def test_empty_foundation_migration_has_no_domain_tables() -> None:
    migration = (PROJECT_ROOT / "backend/migrations/versions/20260602_0001_empty_foundation.py").read_text()

    assert "create_table" not in migration
    assert "drop_table" not in migration
