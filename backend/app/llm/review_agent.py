"""Multi-agent review pipeline: ClaimExtractor as a tool for TechnicalReviewer.

Builds on the Agents SDK's ``Agent.as_tool()`` pattern to create a
multi-agent review where the TechnicalReviewer agent can call a dedicated
ClaimExtractor agent during review.

Usage::

    from backend.app.llm.review_agent import build_review_agent

    agent = build_review_agent(model="gpt-4o", mcp_servers=[...])
    # Pass to Runner.run_sync() or run_streamed()
"""

from __future__ import annotations

from agents import Agent

from backend.app.llm.prompts import PROMPT_REGISTRY


def _get_prompt(name: str) -> str:
    """Get a prompt system message from the registry."""
    prompt = PROMPT_REGISTRY.get(name)
    if prompt is None:
        return ""
    return prompt.system


def build_claim_extractor_agent(
    model: str = "gpt-4o",
) -> Agent:
    """Create a ClaimExtractor agent for extracting claims from drafts.

    This agent is designed to be used as a tool by the TechnicalReviewer
    agent via ``Agent.as_tool()``.

    Returns:
        An ``Agent`` with the claim_extraction prompt that outputs
        ``ClaimExtractionResult``.
    """
    from backend.app.llm.schemas import ClaimExtractionResult

    return Agent(
        name="ClaimExtractor",
        instructions=_get_prompt("claim_extraction"),
        model=model,
        output_type=ClaimExtractionResult,
    )


def build_review_agent(
    model: str = "gpt-4o",
    mcp_servers: list | None = None,
) -> Agent:
    """Create a TechnicalReviewer agent with ClaimExtractor as a tool.

    The TechnicalReviewer reviews a blog draft for technical accuracy.
    During review, it can call the ClaimExtractor Agent as a tool to
    extract factual claims from the draft for evidence checking.

    Args:
        model: OpenAI model name.
        mcp_servers: Optional list of MCP servers for additional tools.

    Returns:
        An ``Agent`` with the technical_review prompt, the ClaimExtractor
        tool, and optional MCP servers, that outputs ``TechnicalReview``.
    """
    from backend.app.llm.schemas import TechnicalReview

    claim_extractor = build_claim_extractor_agent(model=model)

    # Enhanced system prompt that tells the reviewer about the claim extractor tool
    base_system = _get_prompt("technical_review")
    enhanced_system = (
        base_system
        + "\n\n"
        + "You have access to the **extract_claims** tool. "
        + "Use it to extract factual claims from the draft for evidence checking. "
        + "This will identify quantified metrics, performance comparisons, and "
        + "product capability claims that need evidence before publishing. "
        + "Consider these claims when assessing risk and making your "
        + "approval recommendation."
    )

    return Agent(
        name="TechnicalReviewer",
        instructions=enhanced_system,
        model=model,
        output_type=TechnicalReview,
        tools=[
            claim_extractor.as_tool(
                tool_name="extract_claims",
                tool_description=(
                    "Extract factual claims from a blog draft for evidence checking. "
                    "Call this with the full draft markdown text to identify claims "
                    "that need evidence (metrics, performance comparisons, "
                    "product capability statements)."
                ),
            ),
        ],
        mcp_servers=mcp_servers or []  # Agent requires list, not None
    )
