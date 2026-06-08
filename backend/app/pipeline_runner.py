"""Pipeline runner — orchestrate the full seed pipeline from a single admin endpoint.

Calls existing blog_ideas endpoints via HTTP to localhost.
Returns progress logs plus final URLs.
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

import psycopg
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    AdminIdentity,
    require_admin_identity_with_settings,
    sign_admin_identity,
)
from backend.app.settings import Settings

BACKEND_URL = "http://127.0.0.1:18000"
POLL_INTERVAL_SEC = 2
JOB_TIMEOUT_SEC = 300

FIXED_PROJECT_ID = "project_runner_seed"
FIXED_PROJECT_SLUG = "ai-lab-portal-runner"


class PipelineStep(BaseModel):
    label: str
    status: str  # pending | running | done | skipped | failed
    detail: str | None = None


class PipelineRunResult(BaseModel):
    run_id: str
    steps: list[PipelineStep]
    idea_id: str | None = None
    blog_slug: str | None = None
    blog_post_id: str | None = None
    admin_url: str | None = None
    public_url: str | None = None
    overall_status: str  # completed | failed


# ── HTTP helpers ──


def _admin_headers(settings: Settings, user_id: str = "pipeline_runner") -> dict[str, str]:
    payload = json.dumps(
        {
            "user_id": user_id,
            "email": "admin@example.com",
            "role": "admin",
            "issued_at": int(time.time()),
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return {
        ADMIN_IDENTITY_HEADER: payload,
        ADMIN_SIGNATURE_HEADER: sign_admin_identity(payload, settings.admin_boundary_secret),
        "Content-Type": "application/json",
    }


def _api(method: str, path: str, body: dict | None = None, headers: dict | None = None) -> tuple[int, Any]:
    """Make a HTTP request to the local backend API."""
    data = json.dumps(body).encode() if body is not None else None
    req = Request(f"{BACKEND_URL}{path}", data=data, method=method, headers=headers or {})
    try:
        with urlopen(req, timeout=120) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else None
    except HTTPError as exc:
        raw = exc.read().decode()
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, raw


def _wait_job(task_id: str, label: str, headers: dict) -> None:
    deadline = time.time() + JOB_TIMEOUT_SEC
    while time.time() < deadline:
        status, body = _api("GET", f"/admin/blog-ideas/generation-jobs/{task_id}", headers=headers)
        if status != 200:
            raise RuntimeError(f"{label}: job status ({status})")
        s = body.get("status") if body else None
        if s == "completed":
            return
        if s == "failed":
            raise RuntimeError(f"{label}: job failed — {body.get('error_message')}")
        time.sleep(POLL_INTERVAL_SEC)
    raise TimeoutError(f"{label}: timed out")


def _api_with_wait(method: str, path: str, body: dict | None, label: str, headers: dict) -> Any:
    status, result = _api(method, path, body, headers=headers)
    if status == 202:
        task_id = (result.get("detail") or result or {}).get("task_id")
        if not task_id:
            raise RuntimeError(f"{label}: 202 with no task_id: {result}")
        _wait_job(task_id, label, headers)
        return None
    if 200 <= status < 300:
        return result
    raise RuntimeError(f"{label}: HTTP {status}: {result}")


def _latest_idea_id(headers: dict) -> str:
    status, ideas = _api("GET", "/admin/blog-ideas", headers=headers)
    if status >= 300 or not ideas:
        raise RuntimeError(f"List ideas ({status})")
    return max(ideas, key=lambda r: r.get("created_at", ""))["id"]


# ── Pipeline stages ──


def _approve_stage(steps: list[PipelineStep], idea_id: str, patch_field: str, gen_path: str, label: str, headers: dict) -> None:
    """Approve a gate and trigger generation for the next stage."""
    steps.append(PipelineStep(label=f"Approve {label}", status="running"))
    status, _ = _api("PATCH", f"/admin/blog-ideas/{idea_id}", {patch_field: "approved"}, headers=headers)
    if status >= 300:
        raise RuntimeError(f"Approve {label}: HTTP {status}")
    steps[-1].status = "done"

    steps.append(PipelineStep(label=label, status="running"))
    _api_with_wait("POST", f"/admin/blog-ideas/{idea_id}{gen_path}", {}, label, headers)
    steps[-1].status = "done"


def _skip_stage(steps: list[PipelineStep], approve_label: str, run_label: str) -> None:
    steps.append(PipelineStep(label=approve_label, status="skipped", detail="Already done"))
    steps.append(PipelineStep(label=run_label, status="skipped", detail="Already done"))


# ── Router ──


def create_pipeline_runner_router(settings: Settings) -> APIRouter:
    router = APIRouter(prefix="/admin/pipeline", tags=["admin-pipeline"])

    def require_identity(
        identity_payload: str | None = Header(None, alias=ADMIN_IDENTITY_HEADER),
        signature: str | None = Header(None, alias=ADMIN_SIGNATURE_HEADER),
    ) -> AdminIdentity:
        return require_admin_identity_with_settings(settings, identity_payload, signature)

    @router.post("/run", response_model=PipelineRunResult)
    def run_pipeline(
        project_id: str = FIXED_PROJECT_ID,
        _identity: AdminIdentity = Depends(require_identity),
    ) -> PipelineRunResult:
        """Seed project → generate idea → auto-approve all gates → publish."""
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        steps: list[PipelineStep] = []
        headers = _admin_headers(settings)

        idea_id: str | None = None
        blog_slug: str | None = None
        blog_post_id: str | None = None

        def _err(msg: str) -> PipelineRunResult:
            steps.append(PipelineStep(label="Pipeline failed", status="failed", detail=msg))
            return PipelineRunResult(run_id=run_id, steps=steps, overall_status="failed")

        try:
            # 1. Seed project
            steps.append(PipelineStep(label="Seed project", status="running"))
            db_url = settings.database_url.replace("+psycopg", "").replace("+asyncpg", "")
            conn = psycopg.connect(db_url)
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO projects (id, slug, title, description, content_markdown,
                           status, published_at, created_at, updated_at)
                           VALUES (%s, %s, %s, %s, %s, 'published', now(), now(), now())
                           ON CONFLICT (id) DO NOTHING""",
                        (project_id, FIXED_PROJECT_SLUG, "AI Lab Portal",
                         "Full-stack platform for publishing AI lab work.",
                         "FastAPI + Next.js + Celery.\nSemi-auto orchestration with human gates."),
                    )
                conn.commit()
            finally:
                conn.close()
            steps[-1].status = "done"

            # 2. Generate idea
            steps.append(PipelineStep(label="Generate idea", status="running"))
            payload = {
                "project_name": "AI Lab Portal",
                "project_summary": "Full-stack platform for publishing AI lab work.",
                "ai_capabilities": "Multi-stage LLM pipeline with human approval gates.",
                "technical_highlights": "FastAPI + Next.js + Celery.\nSemi-auto pipeline orchestration.",
                "business_value": "Ships credible B2B content from real engineering context.",
            }
            status, result = _api("POST", "/admin/blog-ideas/generate", payload, headers=headers)
            if status == 202:
                task_id = (result.get("detail") or result).get("task_id")
                _wait_job(task_id, "Idea generation", headers)
                idea_id = _latest_idea_id(headers)
            elif 200 <= status < 300:
                idea_id = result["id"]
            else:
                return _err(f"Generate failed ({status}): {result}")
            steps[-1].status = "done"
            steps[-1].detail = idea_id

            # 3. Approve idea → outline
            _, idea = _api("GET", f"/admin/blog-ideas/{idea_id}", headers=headers)
            if idea and idea.get("status") == "approved" and idea.get("outline_sections"):
                _skip_stage(steps, "Approve Idea", "Generate outline")
            else:
                _approve_stage(steps, idea_id, "status", "/generate-outline", "Generate outline", headers)

            # 4. Approve outline → draft
            _, idea = _api("GET", f"/admin/blog-ideas/{idea_id}", headers=headers)
            if idea and idea.get("outline_status") == "approved" and idea.get("draft_markdown"):
                _skip_stage(steps, "Approve Outline", "Generate draft")
            else:
                _approve_stage(steps, idea_id, "outline_status", "/generate-draft", "Generate draft", headers)

            # 5. Approve draft → technical review
            _, idea = _api("GET", f"/admin/blog-ideas/{idea_id}", headers=headers)
            if idea and idea.get("draft_status") == "approved" and idea.get("technical_review"):
                _skip_stage(steps, "Approve Draft", "Technical review")
            else:
                _approve_stage(steps, idea_id, "draft_status", "/review-technical", "Technical review", headers)

            # 6. Accept review → marketing
            _, idea = _api("GET", f"/admin/blog-ideas/{idea_id}", headers=headers)
            if idea and idea.get("marketing_metadata"):
                _skip_stage(steps, "Approve Review", "Marketing metadata")
            else:
                if not idea or idea.get("technical_review_status") != "approved":
                    steps.append(PipelineStep(label="Approve Review", status="running"))
                    _api("PATCH", f"/admin/blog-ideas/{idea_id}", {"technical_review_status": "approved"}, headers=headers)
                    steps[-1].status = "done"
                steps.append(PipelineStep(label="Marketing metadata", status="running"))
                _api_with_wait("POST", f"/admin/blog-ideas/{idea_id}/generate-marketing", {}, "Marketing", headers)
                steps[-1].status = "done"

            # 7. Approve marketing → extract claims
            _, idea = _api("GET", f"/admin/blog-ideas/{idea_id}", headers=headers)
            _, claims_result = _api("GET", f"/admin/blog-ideas/{idea_id}/claims", headers=headers)
            if claims_result and len(claims_result) > 0:
                _skip_stage(steps, "Approve Marketing", "Extract claims")
            else:
                if not idea or idea.get("marketing_status") != "approved":
                    steps.append(PipelineStep(label="Approve Marketing", status="running"))
                    _api("PATCH", f"/admin/blog-ideas/{idea_id}", {"marketing_status": "approved"}, headers=headers)
                    steps[-1].status = "done"
                steps.append(PipelineStep(label="Extract claims", status="running"))
                _api_with_wait("POST", f"/admin/blog-ideas/{idea_id}/extract-claims", {}, "Extract claims", headers)
                steps[-1].status = "done"

            # 8. Waive claims
            steps.append(PipelineStep(label="Waive claims", status="running"))
            _, claims = _api("GET", f"/admin/blog-ideas/{idea_id}/claims", headers=headers)
            if claims:
                pending = [c for c in claims if c.get("status") == "pending"]
                waived = 0
                for claim in pending:
                    _api("PATCH", f"/admin/blog-ideas/claims/{claim['id']}", {"status": "waived"}, headers=headers)
                    waived += 1
                steps[-1].detail = f"Waived {waived} claim(s)"
            else:
                steps[-1].detail = "No claims to waive"
            steps[-1].status = "done"

            # 9. Publish
            steps.append(PipelineStep(label="Publish to blog", status="running"))
            status, publish = _api("POST", f"/admin/blog-ideas/{idea_id}/publish-to-blog", {}, headers=headers)
            if status >= 300:
                return _err(f"Publish failed ({status}): {publish}")
            blog_slug = (publish or {}).get("slug")
            blog_post_id = (publish or {}).get("blog_post_id")
            steps[-1].status = "done"
            steps[-1].detail = blog_slug

        except RuntimeError as exc:
            return _err(str(exc))
        except TimeoutError as exc:
            return _err(str(exc))

        return PipelineRunResult(
            run_id=run_id,
            steps=steps,
            idea_id=idea_id,
            blog_slug=blog_slug,
            blog_post_id=blog_post_id,
            admin_url=f"/admin/blog-ideas/{idea_id}" if idea_id else None,
            public_url=f"/blog/{blog_slug}" if blog_slug else None,
            overall_status="completed",
        )

    return router
