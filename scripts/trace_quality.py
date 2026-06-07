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

# Canonical agent names. All agents should use one of these when recording traces.
# Names are case-sensitive; lowercase is canonical. If a new agent joins, add it here.
CANONICAL_AGENTS: tuple[str, ...] = (
    "pi",
    "cursor",
    "codex",
    "composer",
    "zed",
    "amp",
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

        # Agent name anomaly check: find non-canonical agent values
        all_agents = conn.execute(
            """
            SELECT agent, COUNT(*) as cnt
            FROM trace
            WHERE agent IS NOT NULL
              AND trim(agent) != ''
            GROUP BY agent
            ORDER BY cnt DESC
            """,
        ).fetchall()

        canonical_lower = {a.lower() for a in CANONICAL_AGENTS}
        canonical_set = set(CANONICAL_AGENTS)
        non_canonical_agents: list[tuple[str, int]] = []
        case_mismatch_agents: list[tuple[str, int, str]] = []
        for row in all_agents:
            agent_val = row["agent"]
            cnt = row["cnt"]
            if agent_val.lower() not in canonical_lower:
                non_canonical_agents.append((agent_val, cnt))
            elif agent_val not in canonical_set:
                case_mismatch_agents.append((agent_val, cnt, agent_val.lower()))

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

        if case_mismatch_agents:
            agent_rows = [["agent", "count", "suggestion"]]
            for agent, cnt, suggestion in case_mismatch_agents:
                agent_rows.append([agent, str(cnt), f"use '{suggestion}' instead"])
            print("\nAgent name casing anomalies:")
            print(table(agent_rows))

        if non_canonical_agents:
            unknown_rows = [["agent", "count"]]
            for agent, cnt in non_canonical_agents:
                unknown_rows.append([agent, str(cnt)])
            print("\nNon-canonical agent names:")
            print(table(unknown_rows))

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
