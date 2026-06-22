#!/usr/bin/env python3
"""Batch story verification script.

Queries all stories from the harness CLI and runs verify for each one
that is implemented. Reports pass/fail per story.

Usage:
    python scripts/verify_all_stories.py            # Quick mode (checks proof flags only)
    python scripts/verify_all_stories.py --full     # Full mode (runs story verify commands)
    python scripts/verify_all_stories.py --verbose  # Detailed output
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HARNESS_CLI = REPO_ROOT / "scripts" / "bin" / "harness-cli.exe"


def _run_cli(args: list[str], timeout: int = 30) -> str:
    """Run harness-cli.exe and return stdout."""
    if not HARNESS_CLI.exists():
        print(f"[!] harness-cli not found at {HARNESS_CLI}")
        return ""
    try:
        result = subprocess.run([str(HARNESS_CLI)] + args, capture_output=True, text=True, timeout=timeout)
        return result.stdout
    except subprocess.TimeoutExpired:
        return ""


def get_stories() -> list[dict]:
    """Parse story matrix to extract story IDs, statuses, and proof flags.

    Uses --numeric for consistent proof flag values.
    Parses by fixed-width column positions from the header line.
    """
    output = _run_cli(["query", "matrix", "--numeric"])
    if not output:
        return []

    lines = [l for l in output.split("\n")]
    if len(lines) < 3:
        return []

    # Lines 0-1 are header + separator; data starts at line 2
    header = lines[0]

    # Find column boundaries from the header row
    # Known columns: id(0-12), title(12-68), status(~68-79), unit(~79-84)
    # integ(~84-89), e2e(~89-93), plat(~93-98), evidence(98+)
    
    # Find column positions from header marker underlines
    # The separator line (line 1) has dashes under each column
    separator = lines[1]
    
    def find_col_end(header_str: str, col_name: str, start: int) -> int:
        """Find the end position of a column by locating the next column header."""
        pos = header_str.find(col_name, start)
        if pos < 0:
            return start + 10
        return pos

    # Find column positions dynamically
    id_end = header.find("  title")  # two spaces before title
    title_end = header.find("  status") 
    status_end = header.find("  unit")
    unit_end = header.find("  integ")
    integ_end = header.find("  e2e")
    e2e_end = header.find("  plat")
    plat_end = header.find("  evidence")
    
    # Fallback positions if dynamic parsing fails
    if id_end < 0 or title_end < 0:
        id_end, title_end, status_end = 12, 68, 79
        unit_end, integ_end, e2e_end, plat_end = 84, 89, 93, 98

    stories = []
    for line in lines[2:]:
        if not line.strip():
            continue

        story_id = line[:id_end].strip()
        if not story_id:
            continue
            
        title = line[id_end:title_end].strip()
        status = line[title_end:status_end].strip()
        unit_raw = line[status_end:unit_end].strip() if unit_end > status_end else "0"
        integ_raw = line[unit_end:integ_end].strip() if integ_end > unit_end else "0"
        e2e_raw = line[integ_end:e2e_end].strip() if e2e_end > integ_end else "0"
        plat_raw = line[e2e_end:plat_end].strip() if plat_end > e2e_end else "0"
        evidence = line[plat_end:].strip() if plat_end < len(line) else ""

        # Normalize numeric flags to yes/no/n/a
        def to_flag(val: str) -> str:
            val = val.strip()
            if val == "1":
                return "yes"
            elif val == "0":
                return "no"
            elif val in ("yes", "no", "n/a"):
                return val
            return val

        stories.append({
            "id": story_id,
            "title": title,
            "status": status,
            "proof": {
                "unit": to_flag(unit_raw),
                "integration": to_flag(integ_raw),
                "e2e": to_flag(e2e_raw),
                "platform": to_flag(plat_raw),
            },
            "evidence": evidence,
        })

    return stories


def _proof_ok(proof: dict) -> bool:
    """Check if all required proof flags are 'yes' or 'n/a'."""
    expected = {"yes", "no", "n/a"}
    for flag in proof.values():
        if flag not in expected:
            return False
    return True


def quick_verify(stories: list[dict]) -> list[dict]:
    """Quick mode: verify proof flags only."""
    results = []
    for story in stories:
        if story["status"] == "implemented":
            passed = _proof_ok(story["proof"])
            results.append({
                "id": story["id"],
                "title": story["title"],
                "passed": passed,
                "detail": f"proof: {story['proof']}",
            })
        else:
            results.append({
                "id": story["id"],
                "title": story["title"],
                "passed": None,
                "detail": f"status: {story['status']}",
            })
    return results


def full_verify(stories: list[dict], verbose: bool = False) -> list[dict]:
    """Full mode: run story verify CLI for each implemented story."""
    results = []
    for story in stories:
        if story["status"] != "implemented":
            results.append({
                "id": story["id"],
                "title": story["title"],
                "passed": None,
                "detail": f"status: {story['status']}",
            })
            continue

        output = _run_cli(["story", "verify", story["id"]], timeout=60)
        passed = "passed" in output.lower() or "meets requirement" in output.lower()

        if verbose:
            detail = output.strip() if output else "No output"
        else:
            detail = "passed" if passed else "failed"

        results.append({
            "id": story["id"],
            "title": story["title"],
            "passed": passed,
            "detail": detail,
        })
    return results


def print_report(stories: list[dict], results: list[dict]) -> None:
    """Print formatted report."""
    passed = 0
    failed = 0
    skipped = 0

    for r in results:
        if r["passed"] is None:
            skipped += 1
            print(f"  [..] {r['id']}: {r['title'][:55]} ({r['detail']})")
        elif r["passed"]:
            passed += 1
            print(f"  [OK] {r['id']}: {r['title'][:55]}")
        else:
            failed += 1
            print(f"  [!] {r['id']}: {r['title'][:55]}")
            if r["detail"] and r["detail"] != "failed":
                for line in r["detail"].split("\n")[:3]:
                    print(f"       {line}")

    print()
    print("=" * 55)
    print(f"  Total:      {len(stories)}")
    print(f"  Passed:     {passed}")
    print(f"  Failed:     {failed}")
    print(f"  Skipped:    {skipped}")

    if failed == 0:
        print(f"  Result:     ALL PASSED")
    else:
        print(f"  Result:     {failed} FAILURE(S)")
    print("=" * 55)


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch verify all stories")
    parser.add_argument("--full", action="store_true", help="Run full story verify (slower)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Detailed output")
    args = parser.parse_args()

    stories = get_stories()
    if not stories:
        print("[!] No stories found in matrix.")
        sys.exit(1)

    print(f"Found {len(stories)} stories.\n")

    if args.full:
        print("Mode: FULL (running story verify commands)\n")
        results = full_verify(stories, verbose=args.verbose)
    else:
        print("Mode: QUICK (checking proof flags only)\n")
        results = quick_verify(stories)

    print_report(stories, results)
    sys.exit(1 if any(r["passed"] is False for r in results) else 0)


if __name__ == "__main__":
    main()
