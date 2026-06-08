"""Deterministic LLM responses for Playwright E2E (no OpenAI calls)."""

from __future__ import annotations

from backend.app.llm.schemas import (
    BlogDraft,
    BlogIdea,
    BlogOutline,
    BlogOutlineSection,
    MarketingMetadata,
    SeoAudit,
    TechnicalReview,
)
from backend.app.llm.service import FakeLLMService, LLMService

_E2E_IDEA = BlogIdea(
    title="E2E Golden Path Blog Idea",
    angle="Semi-auto AI blog pipeline",
    target_reader="Engineering leaders",
    article_goal="Prove generate-to-publish workflow in E2E",
    positioning_notes=["Ground claims in project context", "Human review at each gate"],
)

_E2E_OUTLINE = BlogOutline(
    title="E2E Golden Path Blog Idea",
    outline=[
        BlogOutlineSection(section="Context", points=["Why semi-auto matters"]),
        BlogOutlineSection(section="Workflow", points=["Approve each gate", "Orchestrator runs next stage"]),
    ],
)

_E2E_DRAFT = BlogDraft(
    title="E2E Golden Path Blog Idea",
    markdown=(
        "## Context\n\nSemi-auto keeps humans in the loop.\n\n"
        "## Workflow\n\nThe portal streamlines editorial QA for semi-auto blog pipelines.\n"
    ),
)

_E2E_REVIEW = TechnicalReview(
    overall_risk="low",
    issues=[],
    approval_recommendation="approve",
)

_E2E_MARKETING = MarketingMetadata(
    seo_title="E2E Golden Path Blog Idea",
    meta_description="How the AI Lab Portal semi-auto blog pipeline works end to end.",
    excerpt="Semi-auto blog pipeline from project context to publish.",
    linkedin_post="Ship grounded AI blog posts with human gates.",
    x_post="Semi-auto blog agent: approve, generate, publish.",
    cta="Read the full workflow",
)

_E2E_SEO_AUDIT = SeoAudit(
    overall_score=85.0,
    title_analysis="SEO title is well-optimized at 42 characters with primary keyword included.",
    meta_description_analysis="Meta description is 145 chars, includes target keywords and a clear CTA.",
    heading_structure="Good H1/H2 hierarchy. H2 sections cover key topics with logical flow.",
    keyword_analysis="Primary keyword appears in title, H1, and first paragraph. Secondary keywords present in H2s.",
    readability_assessment="Flesch score ~55 (standard). Sentences average 18 words. Good paragraph breaks.",
    internal_linking="Consider adding 1-2 internal links to related blog posts or case studies.",
    issues=[],
    approval_recommendation="approve",
)


def build_e2e_fake_llm_service() -> LLMService:
    return FakeLLMService(
        {
            "blog_idea": _E2E_IDEA,
            "blog_outline": _E2E_OUTLINE,
            "draft_writer": _E2E_DRAFT,
            "draft_section_writer": _E2E_DRAFT,
            "technical_review": _E2E_REVIEW,
            "marketing_metadata": _E2E_MARKETING,
            "seo_audit": _E2E_SEO_AUDIT,
        }
    )
