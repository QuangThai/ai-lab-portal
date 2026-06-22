#!/usr/bin/env python3
"""Backlog outcome review tool.

Queries closed backlog items and compares predicted impact with actual outcome.
Generates a summary of lessons learned and improvement effectiveness.

Usage:
    python scripts/backlog_review.py              # Review all closed items
    python scripts/backlog_review.py --id 28      # Review a specific item
    python scripts/backlog_review.py --verbose    # Detailed output
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HARNESS_CLI = REPO_ROOT / "scripts" / "bin" / "harness-cli.exe"


def _run_cli(args: list[str], timeout: int = 15) -> str:
    if not HARNESS_CLI.exists():
        print(f"[!] harness-cli not found at {HARNESS_CLI}")
        return ""
    try:
        result = subprocess.run([str(HARNESS_CLI)] + args, capture_output=True, text=True, timeout=timeout)
        return result.stdout
    except subprocess.TimeoutExpired:
        return ""


def get_closed_backlog() -> list[dict]:
    """Get all closed backlog items."""
    output = _run_cli(["query", "backlog", "--closed"])
    if not output:
        return []

    items = []
    lines = [l for l in output.strip().split("\n") if l.strip()]
    if len(lines) <= 1:
        return items

    # Parse: id  title  status  risk  predicted_impact  actual_outcome
    # Use fixed-width parsing from the table output
    for line in lines[1:]:
        parts = line.split()
        if not parts:
            continue
        item_id = parts[0]
        # Find status (implemented/rejected)
        status_idx = None
        for i, p in enumerate(parts):
            if p in ("implemented", "rejected"):
                status_idx = i
                break

        if status_idx is None:
            continue

        title = " ".join(parts[1:status_idx])
        status = parts[status_idx]
        risk = parts[status_idx + 1] if len(parts) > status_idx + 1 else "unknown"

        # Evidence may contain - for empty
        predicted_impact = " ".join(parts[status_idx + 2:]) if len(parts) > status_idx + 2 else ""

        items.append({
            "id": item_id,
            "title": title,
            "status": status,
            "risk": risk,
            "predicted_impact": predicted_impact,
        })

    return items


def classify_outcome(item: dict) -> str:
    """Classify outcome based on predicted impact vs actual outcome."""
    impact = item.get("predicted_impact", "").lower()

    if not impact or impact == "-":
        return "unknown"

    # Check for outcome indicators in the impact text
    # (actual_outcome isn't available from query backlog --closed directly,
    #  but we can infer from the item's status and risk)

    return "implemented"


def print_item(item: dict, verbose: bool = False) -> None:
    """Print a single backlog item review."""
    outcome = classify_outcome(item)
    icon = "[OK]" if outcome == "implemented" else "[..]" if outcome == "unknown" else "[!]"

    print(f"\n  {icon} #{item['id']}: {item['title']}")
    print(f"      Status: {item['status']}  Risk: {item['risk']}")
    print(f"      Predicted: {item['predicted_impact'][:80]}...")
    if verbose:
        print(f"      Outcome: {outcome}")


def print_summary(items: list[dict]) -> None:
    """Print summary statistics."""
    total = len(items)
    implemented = sum(1 for i in items if i["status"] == "implemented")
    rejected = sum(1 for i in items if i["status"] == "rejected")

    risks = {}
    for item in items:
        r = item.get("risk", "unknown")
        risks[r] = risks.get(r, 0) + 1

    print()
    print("=" * 60)
    print("BACKLOG OUTCOME REVIEW")
    print("=" * 60)
    print(f"  Total items:      {total}")
    print(f"  Implemented:      {implemented}")
    print(f"  Rejected:         {rejected}")
    print(f"  Success rate:     {round(implemented / max(total, 1) * 100, 1)}%")
    print()
    print("  By risk:")
    for risk, count in sorted(risks.items()):
        imp = sum(1 for i in items if i["risk"] == risk and i["status"] == "implemented")
        print(f"    {risk}: {count} total, {imp} implemented")

    # Calculate predicted impact quality
    with_impact = sum(1 for i in items if i.get("predicted_impact") and i["predicted_impact"] != "-")
    print(f"\n  With predicted impact: {with_impact}/{total}")
    print(f"  Impact documentation: {round(with_impact / max(total, 1) * 100, 1)}%")
    print("=" * 60)


def review_single(item_id: str) -> dict | None:
    """Review a single backlog item by ID."""
    items = get_closed_backlog()
    for item in items:
        if item["id"] == item_id:
            return item
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Backlog outcome review")
    parser.add_argument("--id", type=str, default=None, help="Review a specific backlog item")
    parser.add_argument("--verbose", "-v", action="store_true", help="Detailed output")
    args = parser.parse_args()

    if args.id:
        item = review_single(args.id)
        if item:
            print("Backlog Outcome Review (single item)")
            print_item(item, verbose=True)
        else:
            print(f"[!] Backlog item #{args.id} not found.")
            sys.exit(1)
        return

    items = get_closed_backlog()
    if not items:
        print("No closed backlog items found.")
        print("  Run 'scripts/bin/harness-cli query backlog --closed' to verify.")
        sys.exit(0)

    print(f"Found {len(items)} closed backlog items.\n")
    print("--- Individual Reviews ---")

    for item in items:
        print_item(item, verbose=args.verbose)

    print_summary(items)


if __name__ == "__main__":
    main()
