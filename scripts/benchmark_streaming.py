#!/usr/bin/env python3
"""Benchmark streaming vs Celery generation paths for all pipeline stages.

This script measures architectural overhead by using mock/fake LLM responses,
so it works without an API key. It captures:

- **Celery path** (uses FakeLLMService in test mode):
  HTTP request → route handler → FakeLLMService → response

- **Streaming path** (uses a lightweight fake SSE endpoint):
  HTTP request → route handler → fake SSE events → event parsing → redirect

Usage:
    # Full benchmark (all stages, 3 runs each)
    python scripts/benchmark_streaming.py

    # Specific stages, 5 runs each
    python scripts/benchmark_streaming.py --runs 5 --stages outline,draft

    # Output as JSON
    python scripts/benchmark_streaming.py --json results.json

    # Only seed test data
    python scripts/benchmark_streaming.py --seed-only
"""

from __future__ import annotations

# Must set env vars BEFORE any backend imports so the Celery app singleton
# is created with the correct test-mode configuration.
import os as _os

_os.environ.setdefault("AI_LAB_LLM_BACKEND", "openai")
_os.environ.setdefault("AI_LAB_LLM_E2E_FAKE", "true")
_os.environ.setdefault("AI_LAB_ENVIRONMENT", "test")

import argparse
import asyncio
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean, stdev
from typing import Any

# ── Stage metadata ───────────────────────────────────────────────────

STAGE_LABELS = {
    "idea": "Blog Idea",
    "outline": "Blog Outline",
    "draft": "Blog Draft",
    "review": "Technical Review",
    "marketing": "Marketing Metadata",
}

CELERY_URLS = {
    "idea": "/admin/blog-ideas/generate",
    "outline": "/admin/blog-ideas/{idea_id}/generate-outline",
    "draft": "/admin/blog-ideas/{idea_id}/generate-draft",
    "review": "/admin/blog-ideas/{idea_id}/review-technical",
    "marketing": "/admin/blog-ideas/{idea_id}/generate-marketing",
}

STREAM_URLS = {
    "idea": "/admin/blog-ideas/generate-stream/idea",
    "outline": "/admin/blog-ideas/{idea_id}/generate-stream/outline",
    "draft": "/admin/blog-ideas/{idea_id}/generate-stream/draft",
    "review": "/admin/blog-ideas/{idea_id}/generate-stream/review",
    "marketing": "/admin/blog-ideas/{idea_id}/generate-stream/marketing",
}

# Fake inputs for the idea generation endpoint
IDEA_INPUTS = {
    "project_name": "AI Lab Benchmark",
    "project_summary": "A benchmarking project for testing streaming pipelines.",
    "ai_capabilities": "Natural language processing, real-time streaming.",
    "technical_highlights": "FastAPI, SSE, Celery, OpenAI Agents SDK.",
    "business_value": "Performance comparison of two architectural patterns.",
}


# ── Data structures ──────────────────────────────────────────────────


@dataclass
class RunResult:
    stage: str
    path: str  # "streaming" | "celery"
    run_number: int
    success: bool = False
    duration_ms: float = 0.0
    time_to_first_token_ms: float = 0.0
    token_count: int = 0
    error: str | None = None


@dataclass
class BenchmarkResults:
    timestamp: str
    runs_per_config: int
    results: list[RunResult] = field(default_factory=list)

    def summary(self) -> list[dict]:
        grouped: dict[tuple[str, str], list[RunResult]] = {}
        for r in self.results:
            grouped.setdefault((r.stage, r.path), []).append(r)

        summaries = []
        for (stage, path), runs in sorted(grouped.items()):
            durations = [r.duration_ms for r in runs if r.success]
            if not durations:
                continue
            tokens = [r.token_count for r in runs if r.success]
            avg_tps = (
                mean(
                    [
                        r.token_count / (r.duration_ms / 1000)
                        for r in runs
                        if r.success and r.duration_ms > 0
                    ]
                )
                if tokens
                else 0
            )
            first_tokens = [
                r.time_to_first_token_ms
                for r in runs
                if r.success and r.time_to_first_token_ms > 0
            ]
            summaries.append(
                {
                    "stage": stage,
                    "path": path,
                    "label": STAGE_LABELS.get(stage, stage),
                    "runs": len(runs),
                    "successful": len(durations),
                    "duration_ms_mean": round(mean(durations), 1),
                    "duration_ms_std": round(stdev(durations), 1)
                    if len(durations) > 1
                    else 0.0,
                    "duration_ms_min": round(min(durations), 1),
                    "duration_ms_max": round(max(durations), 1),
                    "token_count_mean": round(mean(tokens), 1) if tokens else 0.0,
                    "tokens_per_second_mean": round(avg_tps, 1),
                    "time_to_first_token_ms_mean": round(mean(first_tokens), 1)
                    if first_tokens
                    else 0.0,
                }
            )
        return summaries


# ── Runner ────────────────────────────────────────────────────────────


class CeleryBenchRunner:
    """Benchmark the Celery generation path (uses FakeLLMService in test mode)."""

    def __init__(self):
        from backend.app.settings import Settings
        from backend.app.blog_ideas import (
            BlogIdeaCreate,
            BlogIdeaRepository,
            BlogIdeaUpdate,
            OutlineSection,
        )

        self.settings = Settings(environment="test", llm_e2e_fake=True)
        self.repository = BlogIdeaRepository()

        # Create and fully seed a blog idea via the shared repository
        self.repository.create(
            BlogIdeaCreate(
                title="Benchmark: Real-Time AI Streaming vs Celery Task Queue",
                angle="Compare two architectural approaches for AI content generation",
                target_reader="Software engineers and engineering managers",
                article_goal="Help teams choose the right architecture",
            )
        )
        self.idea = self.repository.list_all()[-1]

        # Approve idea
        self.repository.update(
            self.idea.id, BlogIdeaUpdate(status="approved")
        )

        # Set outline (approved)
        self.repository.set_outline(
            self.idea.id,
            [
                OutlineSection(
                    section="Introduction", points=["Context", "Motivation"]
                ),
                OutlineSection(
                    section="Architecture Comparison",
                    points=["Streaming path", "Celery path"],
                ),
                OutlineSection(
                    section="Results",
                    points=["Latency", "Throughput"],
                ),
            ],
            status="approved",
        )

        # Set draft (approved)
        self.repository.set_draft(
            self.idea.id,
            "# Test Draft\n\nBenchmarking content...\n\n## Conclusion",
            status="approved",
        )

        # Set review (approved)
        self.repository.set_technical_review(
            self.idea.id,
            review={
                "overall_risk": "low",
                "issues": [{"severity": "info", "description": "Benchmark review"}],
            },
            status="approved",
        )

        self.idea = self.repository.get_by_id(self.idea.id)

        # Create the FastAPI app with the shared repository so route handlers
        # see the same data.
        from backend.app.main import create_app

        self.app = create_app(self.settings, blog_idea_repository=self.repository)

        # Monkey-patch so the Celery task (which runs inline in test mode)
        # uses our shared repository instead of creating a fresh one.
        import backend.app.tasks as _tasks_mod
        import backend.app.task_support as _ts_mod

        _orig_repo = _ts_mod.idea_repository

        def _shared_repo(settings=None):
            return self.repository

        _ts_mod.idea_repository = _shared_repo
        # Re-import tasks to pick up the patched function
        import importlib

        importlib.reload(_tasks_mod)

    def _admin_headers(self) -> dict[str, str]:
        payload = json.dumps(
            {
                "user_id": "bench_user",
                "email": "bench@example.com",
                "role": "admin",
                "issued_at": int(datetime.now().timestamp()),
            }
        )
        from backend.app.admin_boundary import (
            ADMIN_IDENTITY_HEADER,
            ADMIN_SIGNATURE_HEADER,
            sign_admin_identity,
        )

        return {
            ADMIN_IDENTITY_HEADER: payload,
            ADMIN_SIGNATURE_HEADER: sign_admin_identity(
                payload, self.settings.admin_boundary_secret.get_secret_value()
            ),
        }

    def run(self, stage: str, run_number: int) -> RunResult:
        result = RunResult(stage=stage, path="celery", run_number=run_number)
        from starlette.testclient import TestClient

        client = TestClient(self.app)
        url = CELERY_URLS[stage].format(idea_id=self.idea.id)
        headers = self._admin_headers()
        payload = IDEA_INPUTS if stage == "idea" else {}

        try:
            start = time.perf_counter()
            response = client.post(url, json=payload, headers=headers)
            result.duration_ms = (time.perf_counter() - start) * 1000
            result.success = response.status_code in (200, 202)
            if not result.success:
                result.error = f"HTTP {response.status_code}"
        except Exception as exc:
            result.error = str(exc)

        return result


class StreamBenchRunner:
    """Benchmark the streaming path using a fake SSE endpoint."""

    def __init__(self, celery_runner: CeleryBenchRunner):
        self.idea = celery_runner.idea
        self.settings = celery_runner.settings
        self._admin_headers = celery_runner._admin_headers

    def run(self, stage: str, run_number: int) -> RunResult:
        """Benchmark the streaming path using a FastAPI SSE endpoint.

        Registers a fake SSE endpoint that simulates the real streaming
        response (token events, save event) to measure HTTP/SSE overhead.
        """
        result = RunResult(stage=stage, path="streaming", run_number=run_number)

        if stage not in STREAM_URLS:
            result.error = f"Unknown stage: {stage}"
            return result

        try:
            from starlette.testclient import TestClient
            from fastapi import FastAPI
            from fastapi.responses import StreamingResponse

            app = FastAPI()

            @app.post(STREAM_URLS[stage].format(idea_id=self.idea.id))
            async def _handler():
                return StreamingResponse(
                    _fake_sse_stream(stage),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                    },
                )

            client = TestClient(app)
            url = STREAM_URLS[stage].format(idea_id=self.idea.id)
            payload = IDEA_INPUTS if stage == "idea" else {}

            start = time.perf_counter()
            first_token = None
            token_chars = 0

            with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    result.error = f"HTTP {response.status_code}"
                    result.duration_ms = (time.perf_counter() - start) * 1000
                    return result

                for line in response.iter_lines():
                    if not line.startswith("data: "):
                        continue
                    raw = line[6:].strip()
                    if not raw:
                        continue
                    try:
                        event = json.loads(raw)
                        if event.get("type") == "token" and first_token is None:
                            first_token = time.perf_counter()
                            result.time_to_first_token_ms = (
                                first_token - start
                            ) * 1000
                        if event.get("type") == "token":
                            token_chars += len(event.get("data", ""))
                        if event.get("type") == "saved":
                            result.success = True
                        if event.get("type") == "error":
                            result.error = event.get("data", "Unknown error")
                    except json.JSONDecodeError:
                        continue

            result.duration_ms = (time.perf_counter() - start) * 1000
            result.token_count = token_chars

            if not result.error and not result.success:
                result.success = True

        except Exception as exc:
            result.error = str(exc)

        return result


async def _fake_sse_stream(stage: str):
    """Generate fake SSE events simulating a streaming generation."""
    fake_tokens = [
        "This ",
        "is ",
        "a ",
        "benchmark ",
        "simulating ",
        "streaming ",
        "content ",
        "generation ",
        "for ",
        "the ",
        stage,
        " stage.",
    ]
    fake_result = {"stage": stage, "content": "Benchmark result content " * 20}

    yield f"data: {json.dumps({'type': 'status', 'status': 'starting', 'data': 'Starting...'})}\n\n"
    await asyncio.sleep(0.001)

    for token in fake_tokens:
        yield f"data: {json.dumps({'type': 'token', 'data': token})}\n\n"
        await asyncio.sleep(0.001)

    yield (
        f"data: {json.dumps({'type': 'result', 'data': fake_result})}\n\n"
    )
    yield (
        f"data: {json.dumps({'type': 'saved', 'idea_id': 'bench_idea', 'redirect_url': '/admin/blog-ideas/bench_idea'})}\n\n"
    )


# ── Console output ───────────────────────────────────────────────────


def print_summary(summaries: list[dict]):
    print(f"\n{'='*70}")
    print(f"  Benchmark Results")
    print(f"{'='*70}\n")

    for s in summaries:
        path_label = "Streaming" if s["path"] == "streaming" else "Celery"
        print(f"  [{s['label']}] {path_label:>12}")
        print(f"    Successful:  {s['successful']}/{s['runs']}")
        print(f"    Duration:    {s['duration_ms_mean']:>8.1f}ms "
              f"(+-{s['duration_ms_std']:.1f})  "
              f"[{s['duration_ms_min']:.0f} - {s['duration_ms_max']:.0f}]")
        if s["time_to_first_token_ms_mean"] > 0:
            print(f"    TTFB:        {s['time_to_first_token_ms_mean']:>8.1f}ms")
        if s["tokens_per_second_mean"] > 0:
            print(f"    Throughput:  {s['tokens_per_second_mean']:>8.1f} chars/s")
        print()

    # Comparison table
    print(f"{'-'*70}")
    print("  Streaming vs Celery Comparison:")
    print(f"  {'Stage':>20} {'Streaming':>10} {'Celery':>10} {'Ratio':>8}")
    print(f"  {'-'*20} {'-'*10} {'-'*10} {'-'*8}")
    for s in sorted(summaries, key=lambda x: (x["stage"], x["path"])):
        stream = next(
            (x for x in summaries if x["stage"] == s["stage"] and x["path"] == "streaming"),
            None,
        )
        celery = next(
            (x for x in summaries if x["stage"] == s["stage"] and x["path"] == "celery"),
            None,
        )
        if not stream:
            break  # No streaming data for this stage
        s_dur = stream["duration_ms_mean"]
        c_dur = celery["duration_ms_mean"] if celery else 0
        ratio = s_dur / c_dur if c_dur > 0 else 0
        label = STAGE_LABELS.get(s["stage"], s["stage"])
        print(f"  {label:>20} {s_dur:>8.1f}ms {c_dur:>8.1f}ms {ratio:>7.2f}x")
    print()


# ── CLI ──────────────────────────────────────────────────────────────


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark streaming vs Celery paths")
    parser.add_argument(
        "--stages",
        default="idea,outline,draft,review,marketing",
        help="Comma-separated stages (default: all)",
    )
    parser.add_argument("--runs", type=int, default=3, help="Runs per config (default: 3)")
    parser.add_argument("--json", help="Output JSON to file")
    parser.add_argument(
        "--seed-only",
        action="store_true",
        help="Only seed test data, then exit",
    )
    parser.add_argument(
        "--streaming-only",
        action="store_true",
        help="Only run streaming benchmarks",
    )
    parser.add_argument(
        "--celery-only",
        action="store_true",
        help="Only run Celery benchmarks",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    stages = [s.strip() for s in args.stages.split(",") if s.strip()]

    celery_runner = CeleryBenchRunner()

    if args.seed_only:
        print(f"Seeded idea: {celery_runner.idea.id}")
        return 0

    results = BenchmarkResults(
        timestamp=datetime.now().isoformat(),
        runs_per_config=args.runs,
    )

    run_streaming = not args.celery_only
    run_celery = not args.streaming_only

    if run_streaming:
        stream_runner = StreamBenchRunner(celery_runner)

    for stage in stages:
        label = STAGE_LABELS.get(stage, stage)
        print(f"\n  [{label}]")

        if run_celery:
            for run in range(1, args.runs + 1):
                r = celery_runner.run(stage, run)
                results.results.append(r)
                ok = "OK" if r.success else "FAIL"
                print(f"    Celery   #{run}: {ok} ({r.duration_ms:.1f}ms)", end="")
                if r.error:
                    print(f" [{r.error}]", end="")
                print()

        if run_streaming:
            for run in range(1, args.runs + 1):
                r = stream_runner.run(stage, run)
                results.results.append(r)
                ok = "OK" if r.success else "FAIL"
                print(f"    Stream   #{run}: {ok} ({r.duration_ms:.1f}ms)", end="")
                if r.time_to_first_token_ms:
                    print(f" [TTFB={r.time_to_first_token_ms:.1f}ms]", end="")
                if r.error:
                    print(f" [{r.error}]", end="")
                print()

    summaries = results.summary()
    print_summary(summaries)

    if args.json:
        with open(args.json, "w") as f:
            json.dump(
                {
                    "timestamp": results.timestamp,
                    "runs_per_config": results.runs_per_config,
                    "stages": summaries,
                },
                f,
                indent=2,
            )
        print(f"  Saved to: {args.json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
