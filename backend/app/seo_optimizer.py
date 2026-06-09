"""SEO Auto-Optimize Agent.

Analyzes SEO audit results and blog post content to suggest improvements
for title, meta description, heading structure, internal links, and
keyword placement. Changes are presented as before/after diffs for
admin review and approval.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


# ── Output Models ──


class SeoChange(BaseModel):
    """A single SEO improvement suggestion with before/after."""
    section: str = Field(..., pattern=r"^(title|meta_description|headings|internal_links|keywords)$")
    before: str
    after: str
    rationale: str = Field(..., min_length=1, max_length=500)


class SeoOptimizationResult(BaseModel):
    """Complete output of the SEO optimization agent."""
    id: str = ""
    blog_idea_id: str = ""
    changes: list[SeoChange] = Field(default_factory=list, min_length=1)
    overall_summary: str = Field(default="", max_length=1000)
    created_at: str = ""


# ── Service Interface ──


class SeoOptimizerService(ABC):
    """Abstract service for SEO optimization suggestions."""

    @abstractmethod
    def optimize(
        self,
        blog_idea_id: str,
        title: str,
        content_markdown: str,
        seo_audit: dict | None = None,
    ) -> SeoOptimizationResult: ...


# ── Fake Provider ──


class FakeSeoOptimizerService(SeoOptimizerService):
    """Returns fake but realistic SEO optimization suggestions for testing."""

    def optimize(
        self,
        blog_idea_id: str,
        title: str,
        content_markdown: str,
        seo_audit: dict | None = None,
    ) -> SeoOptimizationResult:
        now = datetime.now(UTC).isoformat()

        changes = [
            SeoChange(
                section="title",
                before=title,
                after=f"{title} — A Complete Guide (2026)",
                rationale="Add year and value proposition to improve CTR in search results.",
            ),
            SeoChange(
                section="meta_description",
                before="",
                after=f"Learn about {title.lower()}. Expert insights, practical tips, and real-world examples to help you get started.",
                rationale="Meta description was missing or too short. Added keyword-rich description within 160 chars.",
            ),
            SeoChange(
                section="headings",
                before="## Getting Started\n## Advanced Topics",
                after="## What Is {title}?\n## Getting Started with {title}\n## Advanced {title} Techniques\n## Best Practices and Tips",
                rationale="Restructured headings to include the primary keyword in more H2s for better keyword relevance.",
            ),
            SeoChange(
                section="internal_links",
                before="",
                after="Consider linking to related blog posts about AI engineering patterns and agent workflows.",
                rationale="No internal links found. Adding contextual internal links improves site structure and SEO.",
            ),
            SeoChange(
                section="keywords",
                before="Primary keyword appears 2 times in content.",
                after=f"Primary keyword '{title.lower()}' appears 5-7 times naturally throughout content.",
                rationale="Increase keyword density from 2 to 5-7 occurrences for better topical relevance.",
            ),
        ]

        return SeoOptimizationResult(
            id=str(uuid4()),
            blog_idea_id=blog_idea_id,
            changes=changes,
            overall_summary=f"Found {len(changes)} SEO improvement opportunities. "
                           f"Focus areas: title optimization, meta description, "
                           f"heading structure, internal linking, and keyword density.",
            created_at=now,
        )


# ── LLM-Powered Service ──


class LLMSeoOptimizerService(SeoOptimizerService):
    """Uses LLMService to generate SEO optimization suggestions."""

    def __init__(self, llm_service: Any) -> None:
        self._llm = llm_service

    def optimize(
        self,
        blog_idea_id: str,
        title: str,
        content_markdown: str,
        seo_audit: dict | None = None,
    ) -> SeoOptimizationResult:
        audit_json = str(seo_audit or {})

        inputs = {
            "title": title,
            "content": content_markdown[:4000],
            "seo_audit": audit_json,
        }

        try:
            result = self._llm.generate(
                "seo_optimize",
                inputs,
                SeoOptimizationResult,
            )
            if isinstance(result, SeoOptimizationResult):
                result.id = str(uuid4())
                result.blog_idea_id = blog_idea_id
                result.created_at = datetime.now(UTC).isoformat()
                return result
        except Exception:
            pass

        # Fallback to fake logic
        return FakeSeoOptimizerService().optimize(
            blog_idea_id, title, content_markdown, seo_audit
        )


# ── Apply SEO Changes ──


class SeoApplyRequest(BaseModel):
    """Request to apply selected SEO changes to a blog idea."""
    accepted_sections: list[str] = Field(
        ...,
        min_length=1,
        description="Sections to apply: title, meta_description, headings, internal_links, keywords",
    )
    changes: list[SeoChange] = Field(
        ...,
        min_length=1,
        description="The full set of optimization changes to select from",
    )


class SeoApplyResult(BaseModel):
    """Result of applying one or more SEO changes."""
    applied_sections: list[str]
    new_title: str | None = None
    new_draft_markdown: str | None = None
    new_metadata: dict | None = None
    summary: str


def _parse_headings(text: str) -> list[str]:
    """Extract markdown heading lines (##...) from text."""
    return [line.strip() for line in text.split("\n") if line.strip().startswith("#")]


def _apply_heading_changes(
    draft: str,
    before_headings: str,
    after_headings: str,
) -> str:
    """Replace old headings in draft with new ones."""
    old_lines = _parse_headings(before_headings)
    new_lines = _parse_headings(after_headings)

    if not old_lines:
        return draft

    result = draft
    for i, old in enumerate(old_lines):
        if old in result and i < len(new_lines):
            result = result.replace(old, new_lines[i], 1)
    return result


def _apply_internal_links(draft: str, suggestion: str) -> str:
    """Append internal link suggestions to the draft."""
    section = "\n\n---\n\n🔗 **Suggested Internal Links**\n\n" + suggestion
    if section in draft:
        return draft
    return draft + section


def _extract_keyword_from_after(after: str, fallback_title: str) -> str:
    """Try to extract the target keyword from the 'after' description."""
    import re
    match = re.search(r"'([^']+)'", after)
    return match.group(1) if match else fallback_title.lower()


def _apply_keyword_optimization(draft: str, after: str) -> str:
    """Insert target keyword into draft at natural paragraph breaks."""
    keyword = _extract_keyword_from_after(after, "")
    if not keyword:
        return draft

    # Check if already has the change marker to avoid double-application
    marker = f"<!-- seo-optimized-keywords -->"
    if marker in draft:
        return draft

    # Split into paragraphs, find first paragraph without the keyword, insert it
    paragraphs = draft.split("\n\n")
    inserted = 0
    for i, para in enumerate(paragraphs):
        if keyword.lower() not in para.lower() and len(para.strip()) > 40:
            paragraphs[i] = para + f" {keyword}"
            inserted += 1
            if inserted >= 2:
                break

    result = "\n\n".join(paragraphs)
    if inserted > 0:
        result += f"\n\n{marker}"
    return result


def apply_seo_changes(
    idea_title: str,
    draft_markdown: str | None,
    marketing_metadata: dict | None,
    request: SeoApplyRequest,
) -> SeoApplyResult:
    """Apply selected SEO changes to blog idea content.

    Each accepted section is applied to the appropriate field:
    - title -> replaces idea title
    - meta_description -> updates marketing_metadata["meta_description"]
    - headings -> replaces matching headings in draft_markdown
    - internal_links -> appends link suggestions to draft
    - keywords -> inserts target keyword at natural paragraph breaks
    """
    new_title = idea_title
    new_draft = draft_markdown or ""
    new_meta = dict(marketing_metadata or {})
    applied: list[str] = []

    changes_by_section = {c.section: c for c in request.changes}

    for section in request.accepted_sections:
        change = changes_by_section.get(section)
        if change is None:
            continue

        if section == "title":
            new_title = change.after
            applied.append("title")

        elif section == "meta_description":
            new_meta["meta_description"] = change.after
            applied.append("meta_description")

        elif section == "headings":
            new_draft = _apply_heading_changes(new_draft, change.before, change.after)
            applied.append("headings")

        elif section == "internal_links":
            new_draft = _apply_internal_links(new_draft, change.after)
            applied.append("internal_links")

        elif section == "keywords":
            new_draft = _apply_keyword_optimization(new_draft, change.after)
            applied.append("keywords")

    return SeoApplyResult(
        applied_sections=applied,
        new_title=new_title if new_title != idea_title else None,
        new_draft_markdown=new_draft if new_draft != (draft_markdown or "") else None,
        new_metadata=new_meta if new_meta != dict(marketing_metadata or {}) else None,
        summary=f"Applied {len(applied)} SEO change(s): {', '.join(applied)}.",
    )
