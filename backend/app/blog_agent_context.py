"""Helpers for passing rich project context into blog agent LLM stages."""

from __future__ import annotations

from typing import TYPE_CHECKING

from backend.app.blog_ideas import BlogIdea

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine as SAEngine


def _build_source_context(idea: BlogIdea) -> list[str]:
    """Build base context sections from idea metadata and source project."""
    sections = [
        f"Title: {idea.title}",
        f"Angle: {idea.angle}",
        f"Target reader: {idea.target_reader}",
        f"Article goal: {idea.article_goal}",
    ]
    if idea.positioning_notes:
        sections.append(f"Positioning notes: {'; '.join(idea.positioning_notes)}")

    ctx = idea.source_project_context
    if ctx:
        sections.append("--- Source project (ground truth for examples) ---")
        for key, label in (
            ("project_name", "Project name"),
            ("project_summary", "Summary"),
            ("ai_capabilities", "AI capabilities"),
            ("technical_highlights", "Technical highlights"),
            ("business_value", "Business value"),
        ):
            value = ctx.get(key)
            if value:
                sections.append(f"{label}:\n{value}")

    return sections


def build_project_context(idea: BlogIdea, engine: "SAEngine | None" = None) -> str:
    """Assemble idea metadata plus enriched knowledge for LLM prompts.

    If *engine* is provided, the Knowledge Collector queries the database
    for related projects, blog posts, showcases, and news to enrich context.
    """
    sections = _build_source_context(idea)

    if engine is not None:
        try:
            from backend.app.knowledge_collector import KnowledgeService

            project_name = ""
            if idea.source_project_context:
                project_name = idea.source_project_context.get("project_name", "")

            if project_name:
                ks = KnowledgeService(engine)
                collected = ks.collect_for_project(project_name)
                enriched = collected.to_prompt_context()
                if enriched.strip():
                    sections.append("--- Enriched context (from Knowledge Collector) ---")
                    sections.append(enriched)
        except Exception:
            pass

    return "\n\n".join(sections)
