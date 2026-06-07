"""Post-generation guardrails for the Agents SDK LLM service (US-095).

Uses native Agents SDK ``@output_guardrail`` decorators so guardrails integrate
directly with the agent execution pipeline instead of being called manually
after generation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from agents import GuardrailFunctionOutput, OutputGuardrail, output_guardrail

if TYPE_CHECKING:
    from backend.app.blog_claims import BlogClaimsRepository
    from backend.app.blog_ideas import BlogIdeaRepository


def claim_extraction_guardrail(
    claims_repository: BlogClaimsRepository,
    ideas_repository: BlogIdeaRepository,
    idea_id: str,
) -> OutputGuardrail:
    """Create a native Agents SDK output guardrail that extracts claims.

    The guardrail runs after the ``technical_review`` agent generates its
    output. It reads the associated idea's draft and extracts claims using
    heuristic pattern matching (no extra LLM call).

    Unlike the previous manual guardrail system, this returns a proper
    ``OutputGuardrail`` that the SDK executes as part of the agent run.

    Args:
        claims_repository: Repository to store extracted claims.
        ideas_repository: Repository to fetch the idea and its draft.
        idea_id: The blog idea ID passed through from the service's entity_id.
    """

    @output_guardrail(name="claim_extraction")
    async def _guardrail(
        context: Any,
        agent: Any,
        output: Any,
    ) -> GuardrailFunctionOutput:
        if not idea_id:
            return GuardrailFunctionOutput(
                output_info="no idea_id — skipping claim extraction",
                tripwire_triggered=False,
            )

        idea = ideas_repository.get_by_id(idea_id)
        if idea is None or not idea.draft_markdown:
            return GuardrailFunctionOutput(
                output_info="no draft or idea not found — skipping claim extraction",
                tripwire_triggered=False,
            )

        from backend.app.blog_claims import heuristic_claims_from_draft

        claims = heuristic_claims_from_draft(idea_id, idea.draft_markdown)
        if claims:
            claims_repository.replace_for_idea(idea_id, claims)

        return GuardrailFunctionOutput(
            output_info=f"extracted {len(claims)} claims from technical review",
            tripwire_triggered=False,
        )

    return _guardrail
