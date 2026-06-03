"""Tests for AI runs, generation jobs, and claim ledger (US-033–035)."""

import json
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    sign_admin_identity,
)
from backend.app.ai_runs import AiRunRepository
from backend.app.blog import BlogRepository
from backend.app.blog_claims import (
    BlogClaim,
    BlogClaimsRepository,
    BlogClaimUpdate,
    claims_from_extraction,
)
from backend.app.blog_ideas import BlogIdeaCreate, BlogIdeaRepository, BlogIdeaUpdate, OutlineSection
from backend.app.blog_publish import publish_idea_to_blog
from backend.app.generation_jobs import GenerationJobRepository
from backend.app.llm.recording import RecordingLLMService
from backend.app.llm.schemas import BlogOutline, ClaimExtractionResult, ExtractedClaim
from backend.app.llm.service import FakeLLMService
from backend.app.main import create_app
from backend.app.settings import Settings
from backend.tests.test_blog_publish import _admin_headers, _marketing_metadata, _ready_idea, _test_settings

TEST_SECRET = "test-admin-boundary-secret-at-least-32-chars"


class TestAiRunRecording:
    def test_recording_service_persists_run(self) -> None:
        recorder = AiRunRepository()
        fake = FakeLLMService({"blog_outline": BlogOutline(title="T", outline=[])})
        service = RecordingLLMService(
            fake, recorder, entity_type="blog_idea", entity_id="idea_1"
        )
        service.generate(
            "blog_outline",
            inputs={
                "title": "T",
                "angle": "A",
                "target_reader": "CTO",
                "article_goal": "Explain",
                "positioning_notes": "",
            },
            output_schema=BlogOutline,
        )
        runs = recorder.list_for_entity("blog_idea", "idea_1")
        assert len(runs) == 1
        assert runs[0].prompt_name == "blog_outline"
        assert runs[0].status == "completed"


class TestGenerationJobs:
    def test_job_lifecycle(self) -> None:
        jobs = GenerationJobRepository()
        job = jobs.create_queued(
            blog_idea_id="idea_1", stage="outline", celery_task_id="task-abc"
        )
        assert job.status == "queued"
        running = jobs.mark_running("task-abc")
        assert running is not None
        assert running.status == "running"
        done = jobs.mark_completed("task-abc")
        assert done is not None
        assert done.status == "completed"

    def test_generation_job_api(self) -> None:
        jobs = GenerationJobRepository()
        jobs.create_queued(
            blog_idea_id="idea_x", stage="draft", celery_task_id="celery-123"
        )
        app = create_app(
            settings=_test_settings(),
            generation_job_repository=jobs,
        )
        client = TestClient(app)
        response = client.get(
            "/admin/blog-ideas/generation-jobs/celery-123",
            headers=_admin_headers(),
        )
        assert response.status_code == 200
        assert response.json()["status"] == "queued"


class TestClaimLedger:
    def test_publish_blocked_by_pending_claim(self) -> None:
        ideas_repo = BlogIdeaRepository()
        blog_repo = BlogRepository(posts=[])
        claims_repo = BlogClaimsRepository()
        idea = _ready_idea(ideas_repo)
        claims_repo.replace_for_idea(
            idea.id,
            [
                BlogClaim(
                    id="claim_1",
                    blog_idea_id=idea.id,
                    claim_text="Improved throughput by 50%",
                    claim_type="quantified",
                    status="pending",
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
            ],
        )
        client = TestClient(
            create_app(
                settings=_test_settings(),
                blog_repository=blog_repo,
                blog_idea_repository=ideas_repo,
                claims_repository=claims_repo,
            )
        )
        response = client.post(
            f"/admin/blog-ideas/{idea.id}/publish-to-blog",
            headers=_admin_headers(),
        )
        assert response.status_code == 400
        assert "claim" in response.json()["detail"].lower()

    def test_publish_allowed_when_claim_supported(self) -> None:
        ideas_repo = BlogIdeaRepository()
        blog_repo = BlogRepository(posts=[])
        claims_repo = BlogClaimsRepository()
        idea = _ready_idea(ideas_repo)
        claims_repo.replace_for_idea(
            idea.id,
            [
                BlogClaim(
                    id="claim_1",
                    blog_idea_id=idea.id,
                    claim_text="Improved throughput by 50%",
                    claim_type="quantified",
                    status="supported",
                    evidence_source_type="measurement",
                    evidence_reference="Internal benchmark Q1",
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
            ],
        )
        post_id, slug, already = publish_idea_to_blog(
            idea.id, ideas_repo, blog_repo, claims_repository=claims_repo
        )
        assert already is False
        assert slug

    def test_extract_claims_endpoint(self) -> None:
        ideas_repo = BlogIdeaRepository()
        claims_repo = BlogClaimsRepository()
        idea = ideas_repo.create(
            BlogIdeaCreate(
                title="Claims",
                angle="Test",
                target_reader="Devs",
                article_goal="Test",
            )
        )
        ideas_repo.set_draft(idea.id, "We improved latency by 40%.", status="approved")
        extraction = ClaimExtractionResult(
            claims=[
                ExtractedClaim(
                    claim_text="We improved latency by 40%.",
                    claim_type="quantified",
                    requires_evidence=True,
                )
            ]
        )
        claims = claims_from_extraction(idea.id, extraction)
        claims_repo.replace_for_idea(idea.id, claims)
        app = create_app(
            settings=_test_settings(),
            blog_idea_repository=ideas_repo,
            claims_repository=claims_repo,
        )
        client = TestClient(app)
        listed = client.get(
            f"/admin/blog-ideas/{idea.id}/claims",
            headers=_admin_headers(),
        )
        assert listed.status_code == 200
        assert len(listed.json()) == 1
