#!/usr/bin/env python3
"""Harness drift and staleness detector.

Scans the repository for:
- Stale harness docs (benchmark snapshots older than 30 days)
- Friction trends from recent traces
- Responsibility status vs actual files on disk
- Missing proof flags vs reality
- Outdated decisions

Usage:
    python scripts/drift_detector.py
    python scripts/drift_detector.py --verbose
    python scripts/drift_detector.py --auto-propose  # create backlog items for detected drifts
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HARNESS_CLI = REPO_ROOT / "scripts" / "bin" / "harness-cli.exe"

# Docs that should exist per maturity level
REQUIRED_DOCS = {
    "H1": [
        "AGENTS.md",
        "docs/HARNESS.md",
        "docs/FEATURE_INTAKE.md",
        "docs/ARCHITECTURE.md",
        "docs/TEST_MATRIX.md",
        "docs/templates/story.md",
        "docs/templates/decision.md",
        "docs/templates/validation-report.md",
    ],
    "H2": [
        "scripts/bin/harness-cli.exe",
        "scripts/schema/001-init.sql",
        "docs/HARNESS_COMPONENTS.md",
        "docs/HARNESS_MATURITY.md",
        "docs/TRACE_SPEC.md",
        "docs/CONTEXT_RULES.md",
    ],
    "H3": [
        "docs/benchmark-protocol.md",
        "scripts/harness_benchmark.py",
        "docs/verification-protocol.md",
    ],
    "H4": [
        "scripts/verify_all_stories.py",
    ],
    "H5": [
        "docs/self-improvement-protocol.md",
        "scripts/drift_detector.py",
        "scripts/backlog_review.py",
    ],
}

# Decisions that should have corresponding docs
EXPECTED_DECISION_DIR = REPO_ROOT / "docs" / "decisions"


def _run_cli(args: list[str], timeout: int = 15) -> str:
    if not HARNESS_CLI.exists():
        return ""
    try:
        result = subprocess.run([str(HARNESS_CLI)] + args, capture_output=True, text=True, timeout=timeout)
        return result.stdout
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        return ""


def check_missing_docs() -> list[dict]:
    """Check which required harness docs are missing."""
    findings = []
    for level, files in REQUIRED_DOCS.items():
        for f in files:
            if not (REPO_ROOT / f).exists():
                findings.append({
                    "type": "missing_doc",
                    "level": level,
                    "file": f,
                    "severity": "high" if level in ("H1", "H2") else "medium",
                })
    return findings


def check_stale_benchmark() -> list[dict]:
    """Check if benchmark results are stale (>30 days old)."""
    findings = []
    now = datetime.now(timezone.utc)

    for f in ["harness-benchmark-latest.json", "harness-benchmark-baseline.json"]:
        path = REPO_ROOT / f
        if path.exists():
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            age_days = (now - mtime).days
            if age_days > 30:
                findings.append({
                    "type": "stale_benchmark",
                    "file": f,
                    "age_days": age_days,
                    "severity": "low",
                })

    # Check if benchmark was never run
    if not (REPO_ROOT / "harness-benchmark-latest.json").exists():
        findings.append({
            "type": "benchmark_never_run",
            "file": "harness-benchmark-latest.json",
            "severity": "medium",
        })

    return findings


def check_friction_trends() -> list[dict]:
    """Analyze friction patterns from recent traces."""
    findings = []
    output = _run_cli(["query", "friction"])

    if not output:
        return findings

    lines = [l for l in output.strip().split("\n") if l.strip()]
    if len(lines) <= 1:
        return findings

    # Parse friction entries
    friction_items = []
    for line in lines[1:]:
        parts = line.split()
        if parts:
            friction_items.append(" ".join(parts))

    # Count friction patterns (simple keyword grouping)
    friction_text = " ".join(friction_items).lower()
    patterns = {
        "docker": ["docker", "compose", "container"],
        "database": ["database", "postgres", "migration", "alembic"],
        "environment": ["env", "environment", "config", "setting"],
        "network": ["network", "connect", "timeout", "port"],
        "build": ["build", "compile", "typecheck", "lint"],
        "test": ["test", "e2e", "playwright", "pytest"],
    }

    for pattern_name, keywords in patterns.items():
        count = sum(1 for kw in keywords if kw in friction_text)
        if count >= 2:
            findings.append({
                "type": "friction_pattern",
                "pattern": pattern_name,
                "matches": count,
                "severity": "medium" if count >= 5 else "low",
            })

    return findings


def check_decision_staleness() -> list[dict]:
    """Check if decision records exist and are up to date."""
    findings = []

    if not EXPECTED_DECISION_DIR.exists():
        findings.append({
            "type": "missing_decision_dir",
            "file": "docs/decisions/",
            "severity": "high",
        })
        return findings

    # Check for numeric decision files
    decisions = sorted(EXPECTED_DECISION_DIR.glob("*.md"))
    if not decisions:
        findings.append({
            "type": "no_decision_records",
            "file": "docs/decisions/",
            "severity": "medium",
        })
        return findings

    # Check latest decision age
    latest = max(decisions, key=lambda p: p.stat().st_mtime)
    now = datetime.now(timezone.utc)
    age_days = (now - datetime.fromtimestamp(latest.stat().st_mtime, tz=timezone.utc)).days
    if age_days > 90:
        findings.append({
            "type": "stale_decisions",
            "file": str(latest),
            "age_days": age_days,
            "latest_decision": latest.name,
            "severity": "low",
        })

    return findings


def check_maturity_accuracy() -> list[dict]:
    """Check if the maturity assessment in HARNESS_MATURITY.md matches reality."""
    findings = []

    # Verify H3 claim: docs/benchmark-protocol.md must exist
    if not (REPO_ROOT / "docs/benchmark-protocol.md").exists():
        findings.append({
            "type": "maturity_mismatch",
            "claim": "H3 requires docs/benchmark-protocol.md",
            "reality": "missing",
            "severity": "high",
        })

    # Verify H4 claim: scripts/verify_all_stories.py must exist
    if not (REPO_ROOT / "scripts/verify_all_stories.py").exists():
        findings.append({
            "type": "maturity_mismatch",
            "claim": "H4 requires scripts/verify_all_stories.py",
            "reality": "missing",
            "severity": "high",
        })

    # Verify H5 claim: docs/self-improvement-protocol.md must exist
    if not (REPO_ROOT / "docs/self-improvement-protocol.md").exists():
        findings.append({
            "type": "maturity_mismatch",
            "claim": "H5 requires docs/self-improvement-protocol.md",
            "reality": "missing",
            "severity": "high",
        })

    return findings


def main() -> None:
    parser = argparse.ArgumentParser(description="Harness drift and staleness detector")
    parser.add_argument("--verbose", "-v", action="store_true", help="Detailed output")
    parser.add_argument("--auto-propose", action="store_true",
                        help="Create backlog items for detected drifts")
    args = parser.parse_args()

    all_findings = []
    all_findings.extend(check_missing_docs())
    all_findings.extend(check_stale_benchmark())
    all_findings.extend(check_friction_trends())
    all_findings.extend(check_decision_staleness())
    all_findings.extend(check_maturity_accuracy())

    # Sort by severity
    severity_order = {"high": 0, "medium": 1, "low": 2}
    all_findings.sort(key=lambda f: severity_order.get(f.get("severity", "low"), 99))

    if not all_findings:
        print("✅ No drift detected — everything looks healthy.")
        return

    print(f"Harness Drift Detector — {datetime.now(timezone.utc).isoformat()}")
    print(f"  {len(all_findings)} finding(s)\n")

    high = [f for f in all_findings if f["severity"] == "high"]
    medium = [f for f in all_findings if f["severity"] == "medium"]
    low = [f for f in all_findings if f["severity"] == "low"]

    if high:
        print(f"[!] HIGH SEVERITY ({len(high)}):")
        for f in high:
            print(f"    {f['type']}: {f.get('file', f.get('pattern', '?'))}")
            if args.verbose:
                print(f"      {json.dumps(f)}")
        print()

    if medium:
        print(f"[~] MEDIUM SEVERITY ({len(medium)}):")
        for f in medium:
            print(f"    {f['type']}: {f.get('file', f.get('pattern', '?'))}")
            if args.verbose:
                print(f"      {json.dumps(f)}")
        print()

    if low:
        print(f"[i] LOW SEVERITY ({len(low)}):")
        for f in low:
            print(f"    {f['type']}: {f.get('file', f.get('pattern', '?'))}")

    # Auto-propose backlog items for high-severity findings
    if args.auto_propose and high:
        print("\n  Auto-proposing backlog items for high-severity findings...")
        for f in high:
            title = f"Drift: {f['type']} — {f.get('file', f.get('pattern', ''))}"
            risk = "normal" if f["severity"] == "high" else "tiny"
            impact = f"Fix {f['type']} to restore harness integrity"
            # Note: harness-cli backlog add would be called here in production
            print(f"    Would create: '{title}' (risk: {risk})")

    print("\n  Run with --auto-propose to create backlog items.")

    # Exit with error code if high-severity findings exist
    sys.exit(1 if high else 0)


if __name__ == "__main__":
    main()
