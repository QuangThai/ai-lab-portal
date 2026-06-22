#!/usr/bin/env python3
"""Harness benchmark comparison tool.

Compares two benchmark snapshots to detect regressions and improvements
across all 11 harness responsibilities and 5 benchmark dimensions.

Usage:
    python scripts/harness_benchmark_compare.py --baseline baseline.json --current latest.json
    python scripts/harness_benchmark_compare.py  # uses harness-benchmark-baseline.json and harness-benchmark-latest.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def _classify_change(before: str, after: str) -> str:
    """Classify responsibility status change."""
    levels = {"missing": 0, "partial": 1, "covered": 2}
    b = levels.get(before, -1)
    a = levels.get(after, -1)
    if b == -1 or a == -1:
        return "unknown"
    if b == a:
        return "unchanged"
    if a > b:
        return "IMPROVED" if b < 2 else "unchanged"  # Already at max
    return "REGRESSION"


def _print_dimension_table(base: dict, curr: dict) -> list[str]:
    """Print a comparison table of benchmark dimensions."""
    regressions = []
    dims = ["compliance", "trace_quality", "lane_accuracy", "friction_capture", "verification_health"]
    
    print(f"{'Dimension':<25} {'Baseline':<12} {'Current':<12} {'Change':<10}")
    print("-" * 60)
    
    for dim in dims:
        base_score = base.get("dimensions", {}).get(dim, {}).get("score", 0)
        curr_score = curr.get("dimensions", {}).get(dim, {}).get("score", 0)
        if isinstance(base_score, float) or isinstance(base_score, int):
            diff = round(curr_score - base_score, 2)
            diff_str = f"+{diff}" if diff > 0 else str(diff)
            arrow = "up" if diff > 0 else "down" if diff < 0 else "~"
            if diff < -5:
                regressions.append(f"{dim}: {base_score} -> {curr_score} ({diff})")
            print(f"{dim:<25} {base_score:<12} {curr_score:<12} {diff_str} {arrow}")
        else:
            print(f"{dim:<25} {str(base_score):<12} {str(curr_score):<12} ~")
    
    return regressions


def _print_responsibility_table(base: dict, curr: dict) -> list[str]:
    """Print a comparison table of responsibility statuses and detect regressions."""
    regressions = []
    improvements = []
    
    responsibilities = [
        "task_specification", "context_selection", "tool_access",
        "project_memory", "task_state", "observability",
        "failure_attribution", "verification", "permissions",
        "entropy_auditing", "intervention_recording",
    ]
    
    print(f"\n{'Responsibility':<30} {'Before':<12} {'After':<12} {'Change':<12}")
    print("-" * 68)
    
    for resp in responsibilities:
        before = base.get("responsibility_scores", {}).get(resp, "missing")
        after = curr.get("responsibility_scores", {}).get(resp, "missing")
        change = _classify_change(before, after)
        
        if change == "REGRESSION":
            regressions.append(f"{resp}: {before} -> {after}")
        elif change == "IMPROVED":
            improvements.append(f"{resp}: {before} -> {after}")
        
        print(f"{resp:<30} {before:<12} {after:<12} {change:<12}")
    
    return regressions, improvements


def compare(base_path: str, current_path: str) -> int:
    """Compare two benchmark snapshots. Returns exit code (0 = no regressions, 1 = regressions found)."""
    base = _load(base_path)
    curr = _load(current_path)
    
    print(f"Harness Benchmark Comparison")
    print(f"  Baseline: {base.get('timestamp', 'unknown')}")
    print(f"  Current:  {curr.get('timestamp', 'unknown')}")
    print()
    
    # Compare dimensions
    dim_regressions = _print_dimension_table(base, curr)
    
    # Compare responsibilities
    resp_regressions, improvements = _print_responsibility_table(base, curr)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    if improvements:
        print(f"\nImprovements ({len(improvements)}):")
        for imp in improvements:
            print(f"  [+] {imp}")
    
    if dim_regressions:
        print(f"\nDimension regressions ({len(dim_regressions)}):")
        for reg in dim_regressions:
            print(f"  [!] {reg}")
    
    if resp_regressions:
        print(f"\nResponsibility regressions ({len(resp_regressions)}):")
        for reg in resp_regressions:
            print(f"  [!] {reg}")
    
    if not dim_regressions and not resp_regressions:
        if improvements:
            print("\n  No regressions detected. Improvements found.")
        else:
            print("\n  No changes detected.")
        return 0
    
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare harness benchmark snapshots")
    parser.add_argument("--baseline", "-b", default="harness-benchmark-baseline.json",
                        help="Baseline benchmark file (default: harness-benchmark-baseline.json)")
    parser.add_argument("--current", "-c", default="harness-benchmark-latest.json",
                        help="Current benchmark file (default: harness-benchmark-latest.json)")
    args = parser.parse_args()
    
    base_path = args.baseline
    curr_path = args.current
    
    if not Path(base_path).exists():
        print(f"Baseline not found: {base_path}")
        print("Run 'python scripts/harness_benchmark.py' first to create a baseline.")
        sys.exit(1)
    
    if not Path(curr_path).exists():
        print(f"Current benchmark not found: {curr_path}")
        sys.exit(1)
    
    exit_code = compare(base_path, curr_path)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
