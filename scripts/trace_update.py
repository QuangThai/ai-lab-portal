#!/usr/bin/env python3
"""Update specific fields of an existing Harness trace record.

Usage:
    python scripts/trace_update.py --id 122 --read "file1,file2"
    python scripts/trace_update.py --id 122 --friction "none"
    python scripts/trace_update.py --id 122 --outcome completed

Each --<field> flag sets that column. Comma-separated values are stored as
JSON arrays for list-type fields (actions, read, changed, decisions, errors).

Run with --dry-run to preview changes without writing.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

# Maps CLI flag names to DB column names
FIELD_MAP: dict[str, str] = {
    "summary": "task_summary",
    "intake": "intake_id",
    "story": "story_id",
    "agent": "agent",
    "outcome": "outcome",
    "duration": "duration_seconds",
    "tokens": "token_estimate",
    "friction": "harness_friction",
    "notes": "notes",
    "actions": "actions_taken",
    "read": "files_read",
    "changed": "files_changed",
    "decisions": "decisions_made",
    "errors": "errors",
}

# Fields that expect comma-separated input → JSON array storage
LIST_FIELDS = {"actions", "read", "changed", "decisions", "errors"}

# Integer fields
INT_FIELDS = {"intake", "duration", "tokens"}

# Allowed outcome values
OUTCOMES = {"completed", "blocked", "partial", "failed"}


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "AGENTS.md").exists() and (candidate / "scripts").is_dir():
            return candidate
    return start


def validate_field(field: str, value: str) -> str:
    """Validate and return the SQL value for the given field."""
    if field in INT_FIELDS:
        if not value.strip().isdigit():
            raise ValueError(f"Field --{field} expects an integer, got: {value}")
        return int(value.strip())
    if field == "outcome":
        if value not in OUTCOMES:
            raise ValueError(
                f"Invalid outcome '{value}'. Must be one of: {', '.join(sorted(OUTCOMES))}"
            )
        return value
    if field in LIST_FIELDS:
        parts = [p.strip() for p in value.split(",") if p.strip()]
        import json
        return json.dumps(parts)
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Update a Harness trace record")
    parser.add_argument("--id", type=int, required=True, help="Trace ID to update")
    parser.add_argument("--db", default=None, help="Path to harness.db")

    for flag in FIELD_MAP:
        parser.add_argument(f"--{flag}", default=None, help=f"Set {FIELD_MAP[flag]}")

    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")

    args = parser.parse_args()
    repo_root = find_repo_root(Path.cwd())
    db_path = Path(args.db) if args.db else repo_root / "harness.db"

    if not db_path.exists():
        raise SystemExit(f"Harness database not found: {db_path}")

    # Collect non-None fields
    updates: dict[str, str] = {}
    for flag, col in FIELD_MAP.items():
        val = getattr(args, flag, None)
        if val is not None:
            updates[col] = val

    if not updates:
        print("No fields to update. Specify at least one --<field> flag.")
        return 0

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row

        # Verify trace exists
        row = conn.execute("SELECT id, task_summary FROM trace WHERE id = ?", (args.id,)).fetchone()
        if row is None:
            print(f"Trace #{args.id} not found.")
            return 1

        summary = row["task_summary"][:60]

        if args.dry_run:
            print(f"[DRY RUN] Would update trace #{args.id}: {summary}")
            for col, raw_val in updates.items():
                validated = validate_field(
                    next(flag for flag, c in FIELD_MAP.items() if c == col),
                    raw_val,
                )
                print(f"  {col} = {repr(validated)}")
            return 0

        # Build SET clause
        set_parts: list[str] = []
        params: list = []
        for col, raw_val in updates.items():
            flag = next(f for f, c in FIELD_MAP.items() if c == col)
            validated = validate_field(flag, raw_val)
            set_parts.append(f"{col} = ?")
            params.append(validated)

        params.append(args.id)
        sql = f"UPDATE trace SET {', '.join(set_parts)} WHERE id = ?"
        conn.execute(sql, params)
        conn.commit()

        import json as _json
        changed_desc = ", ".join(
            f"{col}={_json.dumps(val) if isinstance(val, str) and (col in ('actions_taken','files_read','files_changed','decisions_made','errors')) else repr(val)}"
            for col, val in zip(
                [next(flag for flag, c in FIELD_MAP.items() if c == col) for col, _ in updates.items()],
                [validate_field(next(flag for flag, c in FIELD_MAP.items() if c == col), raw_val) for col, raw_val in updates.items()]
            )
        )

        print(f"Updated trace #{args.id}: {summary}")
        print(f"  Fields changed: {changed_desc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
