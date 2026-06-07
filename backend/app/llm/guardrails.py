"""Post-generation guardrails for the Agents SDK LLM service (US-095).

Guardrails are registered per-prompt on ``AgentsSDKLLMService`` and run
after the LLM generates output. They can extract structured data, validate
output, or trigger side effects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic import BaseModel

    from backend.app.blog_claims import BlogClaimsRepository
    from backend.app.blog_ideas import BlogIdea, BlogIdeaRepository


def claim_extraction_guardrail(
    claims_repository: BlogClaimsRepository,
    ideas_repository: BlogIdeaRepository,
) -> Any:
    """Create a guardrail that extracts claims from a technical review's draft.

    The guardrail is registered for the ``technical_review`` prompt. After
    the LLM generates a technical review, it reads the associated idea's
    draft and extracts claims using heuristic pattern matching (no extra
    LLM call).

    Args:
        claims_repository: Repository to store extracted claims.
        ideas_repository: Repository to fetch the idea and its draft.
    """

    def _guardrail(output: BaseModel, inputs: dict[str, Any]) -> None:
        from backend.app.blog_claims import (
            BlogClaim,
            claims_from_extraction,
            heuristic_claims_from_draft,
        )
        from backend.app.llm.schemas import ClaimExtractionResult, ExtractedClaim

        idea_id = inputs.get("idea_id", "")
        if not idea_id:
            return

        idea = ideas_repository.get_by_id(idea_id)
        if idea is None or not idea.draft_markdown:
            return

        # Extract claims using heuristic (no extra LLM call)
        claims = heuristic_claims_from_draft(idea_id, idea.draft_markdown)
        if claims:
            claims_repository.replace_for_idea(idea_id, claims)

    return _guardrail
