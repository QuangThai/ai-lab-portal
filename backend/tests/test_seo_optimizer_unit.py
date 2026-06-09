"""Tests for seo_optimizer.apply_seo_changes() — per-section accept/reject.

Uses the current API: apply_seo_changes(idea_title, draft_markdown, marketing_metadata, request).
"""
from __future__ import annotations

import pytest

from backend.app.seo_optimizer import (
    SeoChange,
    SeoApplyRequest,
    SeoApplyResult,
    apply_seo_changes,
)


class TestApplySeoChanges:
    def test_apply_title_change(self) -> None:
        result = apply_seo_changes(
            idea_title="Original Title",
            draft_markdown=None,
            marketing_metadata={},
            request=SeoApplyRequest(
                accepted_sections=["title"],
                changes=[SeoChange(section="title", before="Old", after="New SEO Title", rationale="Better title")],
            ),
        )
        assert "title" in result.applied_sections
        assert result.new_title == "New SEO Title"

    def test_apply_meta_description(self) -> None:
        result = apply_seo_changes(
            idea_title="Title",
            draft_markdown=None,
            marketing_metadata={},
            request=SeoApplyRequest(
                accepted_sections=["meta_description"],
                changes=[SeoChange(section="meta_description", before="Old", after="New meta desc", rationale="Better desc")],
            ),
        )
        assert "meta_description" in result.applied_sections
        assert result.new_metadata is not None

    def test_apply_headings_to_draft(self) -> None:
        result = apply_seo_changes(
            idea_title="Title",
            draft_markdown="# Old Heading\n\nSome text.\n\n## Another Old\n\nMore text.",
            marketing_metadata={},
            request=SeoApplyRequest(
                accepted_sections=["headings"],
                changes=[SeoChange(section="headings", before="# Old Heading\n## Another Old", after="# New Heading\n## Another New", rationale="Better hierarchy")],
            ),
        )
        assert "headings" in result.applied_sections
        assert result.new_draft_markdown is not None
        assert "# New Heading" in result.new_draft_markdown
        assert "## Another New" in result.new_draft_markdown

    def test_apply_internal_links(self) -> None:
        result = apply_seo_changes(
            idea_title="Title",
            draft_markdown="# Title\n\nContent here.",
            marketing_metadata={},
            request=SeoApplyRequest(
                accepted_sections=["internal_links"],
                changes=[SeoChange(section="internal_links", before="None", after="- [Related](/related)", rationale="Add links")],
            ),
        )
        assert "internal_links" in result.applied_sections
        assert result.new_draft_markdown is not None
        assert "[Related](/related)" in result.new_draft_markdown

    def test_apply_keywords(self) -> None:
        result = apply_seo_changes(
            idea_title="Title",
            draft_markdown="# Title\n\nContent here with enough text to exceed the forty character threshold for paragraph detection.",
            marketing_metadata={},
            request=SeoApplyRequest(
                accepted_sections=["keywords"],
                changes=[SeoChange(section="keywords", before="None", after="Target keyword: 'seo-optimization'", rationale="Add keywords")],
            ),
        )
        assert "keywords" in result.applied_sections
        assert result.new_draft_markdown is not None
        assert "seo-optimization" in result.new_draft_markdown

    def test_keywords_idempotent(self) -> None:
        """Re-applying keywords should not duplicate the comment marker."""
        draft = "# Title\n\nContent with enough text to exceed the forty char threshold for keyword insertion."
        result1 = apply_seo_changes(
            idea_title="Title",
            draft_markdown=draft,
            marketing_metadata={},
            request=SeoApplyRequest(
                accepted_sections=["keywords"],
                changes=[SeoChange(section="keywords", before="None", after="Target: 'keyword-one'", rationale="Add")],
            ),
        )
        md1 = result1.new_draft_markdown or ""
        assert md1.count("<!-- seo-optimized-keywords -->") == 1
        assert md1 != draft  # draft was modified

        # Apply again on the updated draft — should be a no-op (marker already present)
        result2 = apply_seo_changes(
            idea_title="Title",
            draft_markdown=md1,
            marketing_metadata={},
            request=SeoApplyRequest(
                accepted_sections=["keywords"],
                changes=[SeoChange(section="keywords", before="None", after="Target: 'keyword-two'", rationale="Update")],
            ),
        )
        # new_draft_markdown is None when unchanged from input
        assert result2.new_draft_markdown is None

    def test_empty_accepted_sections(self) -> None:
        with pytest.raises(Exception):  # ValidationError from pydantic
            SeoApplyRequest(accepted_sections=[], changes=[])

    def test_unknown_section_skipped(self) -> None:
        result = apply_seo_changes(
            idea_title="Title",
            draft_markdown=None,
            marketing_metadata={},
            request=SeoApplyRequest(
                accepted_sections=["unknown_section_xyz"],
                changes=[SeoChange(section="title", before="Old", after="New", rationale="Better")],
            ),
        )
        assert "unknown_section_xyz" not in result.applied_sections

    def test_all_five_sections_together(self) -> None:
        result = apply_seo_changes(
            idea_title="Old Title",
            draft_markdown="# Old H1\n\nBody text with enough content to pass the forty character length check for keyword insertion.",
            marketing_metadata={},
            request=SeoApplyRequest(
                accepted_sections=["title", "meta_description", "headings", "internal_links", "keywords"],
                changes=[
                    SeoChange(section="title", before="Old Title", after="New Title", rationale="Better"),
                    SeoChange(section="meta_description", before="Old", after="New meta", rationale="Better"),
                    SeoChange(section="headings", before="# Old H1", after="# New H1", rationale="Better hierarchy"),
                    SeoChange(section="internal_links", before="None", after="- [Link](/x)", rationale="Add link"),
                    SeoChange(section="keywords", before="None", after="Target: 'kw1'", rationale="Add"),
                ],
            ),
        )
        assert len(result.applied_sections) == 5
        assert result.new_title == "New Title"

    def test_result_is_serializable(self) -> None:
        result = apply_seo_changes(
            idea_title="Old",
            draft_markdown=None,
            marketing_metadata={},
            request=SeoApplyRequest(
                accepted_sections=["title"],
                changes=[SeoChange(section="title", before="Old", after="New", rationale="Better")],
            ),
        )
        d = result.model_dump()
        assert isinstance(d, dict)
        assert "applied_sections" in d

    def test_summary_is_present(self) -> None:
        result = apply_seo_changes(
            idea_title="Old",
            draft_markdown=None,
            marketing_metadata={},
            request=SeoApplyRequest(
                accepted_sections=["title"],
                changes=[SeoChange(section="title", before="Old", after="New", rationale="Better")],
            ),
        )
        assert isinstance(result.summary, str)
        assert len(result.summary) > 0

    def test_meta_description_updates_metadata(self) -> None:
        result = apply_seo_changes(
            idea_title="Title",
            draft_markdown=None,
            marketing_metadata={"meta_description": "Old desc", "seo_title": "Test"},
            request=SeoApplyRequest(
                accepted_sections=["meta_description"],
                changes=[SeoChange(section="meta_description", before="Old desc", after="New SEO desc", rationale="Better")],
            ),
        )
        assert result.new_metadata is not None
        assert result.new_metadata.get("meta_description") == "New SEO desc"
