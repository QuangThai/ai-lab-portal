# Harness Benchmark Protocol

A repeatable protocol for measuring harness maturity, detecting regressions,
and tracking progress across H1–H5 levels.

## Overview

The benchmark measures five dimensions of harness health:

| Dimension | What it measures | Max score |
|-----------|-----------------|-----------|
| **Compliance** | % of required files and processes that exist | 100% |
| **Trace quality** | Average trace quality score across recent traces | 3.0 |
| **Lane accuracy** | % of intakes where chosen lane matched the work | 100% |
| **Friction capture** | % of benchmark tasks with friction that have captured friction | 100% |
| **Verification health** | % of stories with passing verification | 100% |

## Running the Benchmark

```bash
# Full benchmark run
python scripts/harness_benchmark.py

# Compare with a previous run
python scripts/harness_benchmark_compare.py --baseline harness-benchmark-2026-06-01.json

# Quick score-trace check
scripts/bin/harness-cli score-trace --id <id>
```

The benchmark saves results to `harness-benchmark-latest.json` in the repo root.

## Dimension Definitions

### 1. Compliance

Checks which required harness files exist. The requirements differ by maturity
level — a repo at H3 is measured against H3 requirements, not H5.

**H1 required files:**
- `AGENTS.md` — agent shim with Harness block
- `docs/HARNESS.md` — human-agent collaboration model
- `docs/FEATURE_INTAKE.md` — risk classification
- `docs/ARCHITECTURE.md` — stack, layering, boundaries
- `docs/TEST_MATRIX.md` — proof columns and status
- `docs/templates/story.md`
- `docs/templates/decision.md`
- `docs/templates/validation-report.md`

**H2 additional files:**
- `scripts/bin/harness-cli` (or .exe) — durable CLI
- `scripts/schema/001-init.sql` — schema definition
- `docs/HARNESS_COMPONENTS.md` — component mapping
- `docs/HARNESS_MATURITY.md` — maturity ladder
- `docs/TRACE_SPEC.md` — trace field specification
- `docs/CONTEXT_RULES.md` — phase/lane context rules

**H3 additional files:**
- `docs/benchmark-protocol.md` — this document
- `scripts/harness_benchmark.py` — benchmark runner
- `scripts/harness_benchmark_compare.py` — comparison tool
- `docs/verification-protocol.md` — verification protocol (H4)

**Score calculation:**
```
compliance = (files_present / total_required) × 100
```

### 2. Trace Quality

Averaged from the output of `scripts/bin/harness-cli score-trace` across the
last 20 normal-lane traces. The score reflects completeness against the
trace quality tiers defined in `docs/TRACE_SPEC.md`:

| Tier | Score |
|------|-------|
| Detailed | 3.0 |
| Standard | 2.0 |
| Minimal | 1.0 |

### 3. Lane Accuracy

Measures how often the chosen risk lane (tiny, normal, high-risk) matched the
work's actual complexity. Measured by reviewing intake records against actual
outcomes.

A lane is accurate when:
- **Tiny**: implemented as direct patch, proof via quick checks
- **Normal**: implemented with story file, validation expectations
- **High-risk**: implemented with high-risk story, full proof suite

**Score calculation:**
```
lane_accuracy = (accurate_intakes / total_reviewed_intakes) × 100
```

### 4. Friction Capture

Measures whether harness friction was recorded when it occurred. Computed by
reviewing recent traces linked to intake records with friction, and checking
if `harness_friction` was recorded.

**Score calculation:**
```
friction_capture = (traces_with_friction / tasks_with_friction) × 100
```

### 5. Verification Health

Measures what percentage of stories have passing verification commands.

**Score calculation:**
```
verification_health = (stories_with_passing_verify / stories_with_verify_commands) × 100
```

## Benchmark Output Format

```json
{
  "timestamp": "2026-06-22T10:00:00Z",
  "harness_maturity_target": "H4",
  "dimensions": {
    "compliance": {
      "score": 92.3,
      "files_present": 24,
      "files_required": 26,
      "missing_files": ["docs/verification-protocol.md"]
    },
    "trace_quality": {
      "score": 2.4,
      "traces_scored": 20,
      "method": "harness-cli score-trace average"
    },
    "lane_accuracy": {
      "score": 85.0,
      "accurate": 17,
      "total": 20
    },
    "friction_capture": {
      "score": 80.0,
      "captured": 8,
      "expected": 10
    },
    "verification_health": {
      "score": 75.0,
      "passing": 6,
      "with_verify_commands": 8
    }
  },
  "responsibility_scores": {
    "task_specification": "covered",
    "context_selection": "covered",
    "tool_access": "partial",
    "project_memory": "covered",
    "task_state": "covered",
    "observability": "partial",
    "failure_attribution": "partial",
    "verification": "covered",
    "permissions": "partial",
    "entropy_auditing": "partial",
    "intervention_recording": "partial"
  }
}
```

## Interpreting Results

### Good benchmark
- **Compliance** > 90%
- **Trace quality** ≥ 2.3 (H3 target) or ≥ 2.5 (H4+ target)
- **Lane accuracy** ≥ 80%
- **Friction capture** ≥ 60%
- **Verification health** ≥ 80%

### Needs attention
- **Compliance** dropped > 5% from baseline → document which files were removed
- **Trace quality** dropped > 0.3 → review trace recording checklist
- **Lane accuracy** dropped > 10% → review intake training
- **Friction capture** dropped > 20% → remind agents to record friction
- **Verification health** dropped > 15% → check which stories broke

## Baseline and History

The first benchmark run creates `harness-benchmark-baseline.json`.
Subsequent runs create dated snapshots.
Compare current vs baseline to detect regressions:

```bash
python scripts/harness_benchmark_compare.py \
  --baseline harness-benchmark-baseline.json \
  --current harness-benchmark-latest.json
```

## Integration with Maturity Ladder

| Level | Minimum benchmark threshold | Benchmark file must exist |
|-------|---------------------------|--------------------------|
| H1 | Compliance ≥ 70% | No |
| H2 | Compliance ≥ 80%, trace quality ≥ 2.0 | No |
| H3 | Compliance ≥ 85%, trace quality ≥ 2.3, lane accuracy ≥ 80% | Yes — `docs/benchmark-protocol.md` + `scripts/harness_benchmark.py` |
| H4 | All of H3 plus compliance ≥ 90%, verification health ≥ 80% | Yes — H3 files + `docs/verification-protocol.md` + batch verification script |
| H5 | All of H4 plus friction capture ≥ 80%, self-improvement protocol exists | Yes — H4 files + self-improvement protocol |

## Responsibility Regression Detection

When comparing two benchmark runs, each responsibility is classified as:

| Change | Label | Action |
|--------|-------|--------|
| No change | — | — |
| covered → partial | **Regression** | Investigate which file or process was removed |
| partial → covered | **Improvement** | Note what was added |
| covered → missing | **Critical regression** | Requires immediate fix |
| missing → partial | **Progress** | Acknowledge the step forward |

The comparison script outputs a table of all 11 responsibilities with their
before/after status and a regression flag.
