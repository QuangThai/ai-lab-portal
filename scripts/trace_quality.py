#!/usr/bin/env python3
"""Audit Harness trace completeness.

This companion script reports the same trace-quality gaps that otherwise require
ad hoc SQL against `harness.db`. It is intentionally dependency-free so agents can
run it before final trace cleanup.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

CORE_CHECKS: tuple[tuple[str, str], ...] = (
    ("missing_outcome", "outcome IS NULL OR trim(outcome) = ''"),
    ("missing_friction", "harness_friction IS NULL OR trim(harness_friction) = ''"),
    ("missing_agent", "agent IS NULL OR trim(agent) = ''"),
    ("missing_actions", "actions_taken IS NULL OR trim(actions_taken) = ''"),
    ("missing_read", "files_read IS NULL OR trim(files_read) = ''"),
    ("missing_changed", "files_changed IS NULL OR trim(files_changed) = ''"),
)

ADVISORY_CHECKS: tuple[tuple[str, str], ...] = (
    # Trace spec only expects intake_id when an intake was recorded. Treat this as
    # an advisory linkage gap instead of an incomplete trace so historical traces
    # are not forced onto the wrong intake.
    ("missing_intake", "intake_id IS NULL"),
)


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "AGENTS.md").exists() and (candidate / "scripts").is_dir():
            return candidate
    return start


def table(rows: list[list[str]]) -> str:
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    lines: list[str] = []
    for index, row in enumerate(rows):
        lines.append("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))
        if index == 0:
            lines.append("  ".join("-" * width for width in widths))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Harness trace completeness")
    parser.add_argument("--db", default=None, help="Path to harness.db (defaults to repo root/harness.db)")
    parser.add_argument("--limit", type=int, default=20, help="Maximum incomplete trace rows to print")
    args = parser.parse_args()

    repo_root = find_repo_root(Path.cwd())
    db_path = Path(args.db) if args.db else repo_root / "harness.db"
    if not db_path.exists():
        raise SystemExit(f"Harness database not found: {db_path}")

    core_where_any = " OR ".join(f"({condition})" for _, condition in CORE_CHECKS)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        total = conn.execute("SELECT count(*) FROM trace").fetchone()[0]
        core_summary = []
        for name, condition in CORE_CHECKS:
            count = conn.execute(f"SELECT count(*) FROM trace WHERE {condition}").fetchone()[0]
            core_summary.append([name, str(count)])

        advisory_summary = []
        for name, condition in ADVISORY_CHECKS:
            count = conn.execute(f"SELECT count(*) FROM trace WHERE {condition}").fetchone()[0]
            advisory_summary.append([name, str(count)])

        rows = conn.execute(
            f"""
            SELECT id, outcome, task_summary, harness_friction
            FROM trace
            WHERE {core_where_any}
            ORDER BY id DESC
            LIMIT ?
            """,
            (args.limit,),
        ).fetchall()

    print(f"Trace quality audit: {total} trace(s)")
    print(table([["core gap", "count"], *core_summary]))
    print("\nAdvisory linkage gaps:")
    print(table([["advisory", "count"], *advisory_summary]))

    if rows:
        detail_rows = [["id", "outcome", "summary", "friction"]]
        for row in rows:
            detail_rows.append([
                str(row["id"]),
                row["outcome"] or "",
                (row["task_summary"] or "")[:72],
                (row["harness_friction"] or "")[:72],
            ])
        print("\nIncomplete traces:")
        print(table(detail_rows))
    else:
        print("\nNo incomplete traces found.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
