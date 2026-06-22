# Self-Improvement Protocol

**H5 — Self-Improving Harness**

The harness can use traces, benchmark results, and backlog outcomes to propose
or apply safe improvements to itself. This protocol defines how the improvement
loop works, what triggers a proposal, and how changes are validated.

## The Improvement Loop

```text
Trace (friction captured)
  → Friction trend detected (3+ occurrences)
    → Improvement proposal (backlog item with predicted impact)
      → Review + accept/reject
        → Implement change
          → Benchmark before/after comparison
            → Outcome review (predicted vs actual)
```

Every turn of this loop produces one of three outcomes:
1. **Positive delta** — the change improved the measured dimension.
2. **No delta** — the change had no measurable effect; consider reverting.
3. **Negative delta** — the change regressed a dimension; revert immediately.

## Friction-to-Proposal Pipeline

### Step 1: Detect Friction Patterns

Friction is detected from:

| Source | Tool | Frequency |
|--------|------|-----------|
| Trace `harness_friction` field | `scripts/bin/harness-cli query friction` | On each trace |
| Repeated error patterns | `scripts/drift_detector.py` | Weekly or on-demand |
| Benchmark regressions | `scripts/harness_benchmark_compare.py` | After each benchmark run |
| Stale docs | `scripts/drift_detector.py` | Weekly or on-demand |

A friction pattern is actionable when it has appeared **3+ times** in traces
within a 30-day window.

### Step 2: Create Improvement Proposal

When a friction pattern is actionable, create a backlog item with:

```bash
scripts/bin/harness-cli backlog add \
  --title "<Short action title>" \
  --risk <tiny|normal|high-risk> \
  --predicted-impact "<What change is expected to improve>"
```

Each proposal must include:

| Field | Required | Description |
|-------|----------|-------------|
| **Title** | Yes | Short, actionable name |
| **Risk** | Yes | tiny, normal, or high-risk |
| **Predicted impact** | Yes | What dimension will improve and by how much |
| **Validation plan** | Yes | How to measure success (benchmark dimension, trace quality, etc.) |
| **Rollback criteria** | Yes | When to revert (negative delta in any dimension) |

### Step 3: High-Risk Change Protocol

Changes classified as **high-risk** must pause for human confirmation before
implementation. High-risk changes include:

- Changing the harness CLI binary or schema
- Changing the maturity ladder or level criteria
- Changing the intake classification policy
- Changing the architecture boundary rules
- Adding or removing required docs from a maturity level

High-risk proposal format:

```bash
scripts/bin/harness-cli backlog add \
  --title "<Short action title>" \
  --risk high-risk \
  --predicted-impact "..." \
  --notes "HIGH-RISK: requires human confirmation before implementation"
```

## Backlog Outcome Review

After a backlog item is implemented, review its outcome:

```bash
# Review a single item
python scripts/backlog_review.py --id <backlog_id>

# Review all closed items
python scripts/backlog_review.py
```

The review compares:
- **Predicted impact** (what the proposal said would happen)
- **Actual outcome** (what actually happened, recorded in `backlog close`)

Outcome classifications:

| Classification | Meaning |
|----------------|---------|
| **Hit** | Actual outcome matched or exceeded predicted impact |
| **Miss** | Actual outcome fell short of predicted impact |
| **Overshot** | Change was more complex than predicted but delivered more value |
| **Regression** | Change caused harm in another dimension |

## Benchmark-Triggered Improvements

When a benchmark comparison detects a regression (see `harness_benchmark_compare.py`),
it automatically creates a backlog proposal for investigation:

```bash
# After detecting a regression:
python scripts/drift_detector.py --regression --auto-propose
```

This creates a backlog item with:
- Risk: normal (or high-risk if compliance dropped below 80%)
- Predicted impact: "Restore [dimension] to baseline level"
- Validation plan: "Run benchmark comparison until baseline is matched"

## Rollback Procedure

If a change causes a regression:

1. **Stop**: Halt any further changes to the affected area.
2. **Assess**: Run `scripts/harness_benchmark_compare.py` to quantify the damage.
3. **Revert**: `git revert <commit>` for the change.
4. **Verify**: Run benchmark again to confirm baseline is restored.
5. **Document**: Add a trace with friction documenting the failed change.

## Scope Creep Prevention

To prevent scope creep and validation weakening:

1. **Every proposal has one measurable goal.** If a proposal says "improve
   trace quality", it must specify "from X to Y" with a timeframe.
2. **Benchmark before implementing.** Always run the benchmark before applying
   a harness change to establish the baseline.
3. **Compare after implementing.** Run the benchmark again after the change.
4. **Reject multi-goal proposals.** If a proposal has multiple unrelated
   predicted impacts, split it into separate backlog items.
5. **Validation plans must be specific.** "Run the benchmark" is specific.
   "Make the harness better" is not.

## Historical Records

All improvement proposals, implementations, and outcome reviews are recorded in:

| Artifact | Location | Purpose |
|----------|----------|---------|
| Backlog items | `harness.db` (via CLI) + `docs/HARNESS_BACKLOG.md` | Proposals and outcomes |
| Traces | `harness.db` (via CLI) | Execution records |
| Benchmark snapshots | `harness-benchmark-*.json` | Before/after comparison |
| Improvement reports | `docs/HARNESS_MATURITY.md` | Maturity progression |

## Tools Reference

| Tool | Purpose | Frequency |
|------|---------|-----------|
| `scripts/harness_benchmark.py` | Run benchmark snapshot | Before/after each harness change |
| `scripts/harness_benchmark_compare.py` | Compare two snapshots | After each benchmark run |
| `scripts/drift_detector.py` | Detect stale docs, friction trends | Weekly |
| `scripts/backlog_review.py` | Review backlog outcomes | Monthly |
| `scripts/verify_all_stories.py` | Batch story verification | Before release |
| `scripts/bin/harness-cli query friction` | Review captured friction | On demand |
