"""Tests for blog_claims.py — claim extraction and evidence ledger."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from backend.app.blog_claims import BlogClaim, BlogClaimUpdate, BlogClaimsRepository
from backend.app.llm.schemas import ClaimExtractionResult


@pytest.fixture
def repo() -> BlogClaimsRepository:
    return BlogClaimsRepository()


def _claim(**overrides) -> BlogClaim:
    now = datetime.now(UTC)
    return BlogClaim(
        id=overrides.get("id", "c1"),
        blog_idea_id=overrides.get("blog_idea_id", "idea_1"),
        claim_text=overrides.get("claim_text", "Test claim"),
        claim_type=overrides.get("claim_type", "performance"),
        status=overrides.get("status", "pending"),
        created_at=overrides.get("created_at", now),
        updated_at=overrides.get("updated_at", now),
    )


class TestBlogClaimsRepository:
    def test_list_empty(self, repo: BlogClaimsRepository):
        assert repo.list_for_idea("idea_1") == []

    def test_replace_for_idea(self, repo: BlogClaimsRepository):
        claims = [_claim(id="c1"), _claim(id="c2")]
        replaced = repo.replace_for_idea("idea_1", claims)
        assert len(replaced) == 2
        assert all(c.blog_idea_id == "idea_1" for c in replaced)

    def test_replace_removes_old_claims(self, repo: BlogClaimsRepository):
        """Previous claims for same idea are replaced."""
        old = [_claim(id="c1")]
        repo.replace_for_idea("idea_1", old)
        new = [_claim(id="c2")]
        replaced = repo.replace_for_idea("idea_1", new)
        assert len(replaced) == 1
        assert replaced[0].id == "c2"

    def test_replace_preserves_other_ideas(self, repo: BlogClaimsRepository):
        c1 = _claim(id="c1", blog_idea_id="idea_1")
        c2 = _claim(id="c2", blog_idea_id="idea_2")
        repo.replace_for_idea("idea_1", [c1])
        repo.replace_for_idea("idea_2", [c2])
        assert len(repo.list_for_idea("idea_1")) == 1
        assert len(repo.list_for_idea("idea_2")) == 1

    def test_get_by_id(self, repo: BlogClaimsRepository):
        claim = _claim(id="c1")
        repo.replace_for_idea("idea_1", [claim])
        fetched = repo.get_by_id("c1")
        assert fetched is not None
        assert fetched.claim_text == "Test claim"

    def test_get_by_id_not_found(self, repo: BlogClaimsRepository):
        assert repo.get_by_id("nonexistent") is None

    def test_update_status(self, repo: BlogClaimsRepository):
        claim = _claim(id="c1", status="pending")
        repo.replace_for_idea("idea_1", [claim])
        updated = repo.update("c1", BlogClaimUpdate(status="supported"))
        assert updated is not None
        assert updated.status == "supported"

    def test_update_not_found(self, repo: BlogClaimsRepository):
        assert repo.update("nonexistent", BlogClaimUpdate(status="supported")) is None

    def test_update_with_evidence_auto_sets_supported(self, repo: BlogClaimsRepository):
        """Providing evidence reference without status should auto-set to supported."""
        claim = _claim(id="c1", status="pending")
        repo.replace_for_idea("idea_1", [claim])
        updated = repo.update("c1", BlogClaimUpdate(evidence_reference="https://data.example.com"))
        assert updated is not None
        assert updated.status == "supported"
        assert updated.evidence_reference == "https://data.example.com"

    def test_update_explicit_status_with_evidence(self, repo: BlogClaimsRepository):
        """Explicit status should override auto-set when evidence is provided."""
        claim = _claim(id="c1", status="pending")
        repo.replace_for_idea("idea_1", [claim])
        updated = repo.update("c1", BlogClaimUpdate(
            status="unsupported",
            evidence_reference="https://example.com",
        ))
        assert updated is not None
        assert updated.status == "unsupported"  # explicit wins over auto-set

    def test_update_evidence_source_type(self, repo: BlogClaimsRepository):
        claim = _claim(id="c1")
        repo.replace_for_idea("idea_1", [claim])
        updated = repo.update("c1", BlogClaimUpdate(evidence_source_type="customer_interview"))
        assert updated is not None
        assert updated.evidence_source_type == "customer_interview"

    def test_list_returns_sorted_by_created_at(self, repo: BlogClaimsRepository):
        earlier = _claim(id="c1", created_at=datetime(2026, 1, 1, tzinfo=UTC))
        later = _claim(id="c2", created_at=datetime(2026, 6, 1, tzinfo=UTC))
        repo.replace_for_idea("idea_1", [later, earlier])
        claims = repo.list_for_idea("idea_1")
        assert claims[0].id == "c1"  # earlier first
        assert claims[1].id == "c2"
