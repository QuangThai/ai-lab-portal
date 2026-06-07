"""Knowledge Collector — enriches AI Blog Agent context from all data sources.

The Knowledge Service queries projects, showcases, blog posts, and news
articles to build a rich context document for the LLM. This reduces
hallucination by grounding generation in real data.

Call order:
1. collect_context(idea_id, project_name) → KnowledgeContext
2. KnowledgeContext.summary → string injected into LLM prompts
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy import Engine, Text, select
from sqlalchemy.engine import Engine as SAEngine
from sqlalchemy.sql import func


# ─── Models ────────────────────────────────────────────────────────────────


class KnowledgeContext(BaseModel):
    """Aggregated knowledge context for a blog idea."""

    id: str
    blog_idea_id: str | None = None
    project_name: str | None = None

    # Source snippets
    project_summary: str | None = None
    project_content_markdown: str | None = None
    project_tech_highlights: list[str] = field(default_factory=list)

    related_blog_posts: list[dict[str, Any]] = field(default_factory=list)
    related_showcases: list[dict[str, Any]] = field(default_factory=list)
    recent_news: list[dict[str, Any]] = field(default_factory=list)

    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class KnowledgeCollectionResult:
    """Result of a knowledge collection run."""

    sources_queried: int = 0
    blog_posts_found: int = 0
    showcases_found: int = 0
    news_found: int = 0
    context_summary: str = ""
    errors: list[str] = field(default_factory=list)

    def to_prompt_context(self) -> str:
        """Build a rich context string for LLM prompts."""
        parts: list[str] = []
        if self.context_summary:
            parts.append(self.context_summary)
        if self.blog_posts_found > 0:
            parts.append(f"\nRelated blog posts available: {self.blog_posts_found}")
        if self.showcases_found > 0:
            parts.append(f"Related showcases available: {self.showcases_found}")
        if self.news_found > 0:
            parts.append(f"Recent news articles on related topics: {self.news_found}")
        return "\n".join(parts)


# ─── Knowledge Service ─────────────────────────────────────────────────────


class KnowledgeService:
    """Aggregates context from all available data sources.

    Call ``collect_for_project()`` to get a rich context document for a
    given project or topic. Used by the AI Blog Agent pipeline stages.
    """

    def __init__(self, engine: SAEngine | None = None) -> None:
        self._engine = engine

    # ── Public API ──────────────────────────────────────────────────────

    def collect_for_project(
        self,
        project_name: str,
        project_summary: str = "",
        project_content: str = "",
    ) -> KnowledgeCollectionResult:
        """Collect knowledge for a project.

        Queries projects, blog posts, showcases, and news for related content.
        """
        result = KnowledgeCollectionResult()
        sources: list[str] = []

        # 1. Query projects table for full content
        if self._engine:
            sources.append("projects")
            project_data = self._query_projects(project_name)
            if project_data:
                result.context_summary += (
                    f"Project: {project_data.get('title', project_name)}\n"
                    f"Description: {project_data.get('description', project_summary)[:500]}\n"
                )
                content = project_data.get("content_markdown", "")
                if content and len(content) > 200:
                    result.context_summary += (
                        f"Full project content ({len(content)} chars):\n"
                        f"{content[:2000]}\n"
                    )

        # 2. Query published blog posts for related content
        if self._engine:
            sources.append("blog_posts")
            related = self._query_related_blog_posts(project_name)
            result.blog_posts_found = len(related)
            if related:
                result.context_summary += "\nRelated published blog posts:\n"
                for post in related[:3]:
                    result.context_summary += (
                        f"- {post.get('title', '')}: "
                        f"{post.get('excerpt', '')[:150]}\n"
                    )

        # 3. Query showcases
        if self._engine:
            sources.append("showcases")
            showcases = self._query_related_showcases(project_name)
            result.showcases_found = len(showcases)
            if showcases:
                result.context_summary += "\nRelated showcases:\n"
                for s in showcases[:2]:
                    result.context_summary += (
                        f"- {s.get('title', '')}: "
                        f"{s.get('hero_summary', '')[:150]}\n"
                    )

        # 4. Query recent news articles
        if self._engine:
            sources.append("news")
            news = self._query_recent_ai_news()
            result.news_found = len(news)
            if news:
                result.context_summary += f"\nRecent AI news ({len(news)} articles available)\n"

        result.sources_queried = len(sources)
        if not result.context_summary:
            result.context_summary = (
                f"Context for '{project_name}': {project_summary[:500]}\n"
                f"Technical details: {project_content[:1000]}\n"
            )
        return result

    def collect_for_idea(self, idea_id: str, project_name: str) -> str:
        """Collect knowledge for an existing blog idea.

        Returns a markdown context string ready for LLM prompts.
        Used by ``build_project_context()`` in later pipeline stages.
        """
        result = self.collect_for_project(project_name)
        return result.to_prompt_context()

    # ── Internal queries ────────────────────────────────────────────────

    def _query_projects(self, project_name: str) -> dict[str, Any] | None:
        """Query the projects table for a matching project."""
        try:
            from backend.app.database import projects as projects_table

            with self._engine.begin() as conn:
                row = conn.execute(
                    select(
                        projects_table.c.title,
                        projects_table.c.description,
                        projects_table.c.content_markdown,
                        projects_table.c.tech_stack,
                        projects_table.c.ai_capabilities,
                        projects_table.c.business_value,
                    )
                    .where(
                        func.lower(projects_table.c.title).like(
                            f"%{project_name.lower()}%"
                        )
                    )
                    .limit(1)
                ).mappings().first()
                if row:
                    return dict(row)
        except Exception:
            return None
        return None

    def _query_related_blog_posts(self, keyword: str) -> list[dict[str, Any]]:
        """Query published blog posts related to a keyword."""
        try:
            from backend.app.database import blog_posts as blog_posts_table

            with self._engine.begin() as conn:
                rows = conn.execute(
                    select(
                        blog_posts_table.c.title,
                        blog_posts_table.c.excerpt,
                        blog_posts_table.c.slug,
                        blog_posts_table.c.published_at,
                    )
                    .where(
                        blog_posts_table.c.status == "published",
                        func.lower(blog_posts_table.c.title).like(
                            f"%{keyword.lower()}%"
                        )
                        | func.lower(blog_posts_table.c.excerpt).like(
                            f"%{keyword.lower()}%"
                        ),
                    )
                    .order_by(blog_posts_table.c.published_at.desc())
                    .limit(5)
                ).mappings()
                return [dict(r) for r in rows if r]
        except Exception:
            return []
        return []

    def _query_related_showcases(self, keyword: str) -> list[dict[str, Any]]:
        """Query published showcases related to a keyword."""
        try:
            from backend.app.database import showcases as showcases_table

            with self._engine.begin() as conn:
                rows = conn.execute(
                    select(
                        showcases_table.c.title,
                        showcases_table.c.hero_summary,
                        showcases_table.c.slug,
                    )
                    .where(
                        showcases_table.c.status == "published",
                        func.lower(showcases_table.c.title).like(
                            f"%{keyword.lower()}%"
                        ),
                    )
                    .limit(3)
                ).mappings()
                return [dict(r) for r in rows if r]
        except Exception:
            return []
        return []

    def _query_recent_ai_news(self, limit: int = 5) -> list[dict[str, Any]]:
        """Query recent AI news articles."""
        try:
            from backend.app.database import news_review_items as news_table

            with self._engine.begin() as conn:
                rows = conn.execute(
                    select(
                        news_table.c.title,
                        news_table.c.ai_summary,
                        news_table.c.published_at,
                    )
                    .where(news_table.c.status == "published")
                    .order_by(news_table.c.published_at.desc())
                    .limit(limit)
                ).mappings()
                return [dict(r) for r in rows if r]
        except Exception:
            return []
        return []


class InMemoryKnowledgeService(KnowledgeService):
    """In-memory knowledge service for tests. Returns limited context."""

    def collect_for_project(
        self,
        project_name: str,
        project_summary: str = "",
        project_content: str = "",
    ) -> KnowledgeCollectionResult:
        return KnowledgeCollectionResult(
            sources_queried=1,
            context_summary=(
                f"Project: {project_name}\n"
                f"Description: {project_summary[:500]}\n"
                f"Content: {project_content[:1000]}\n"
            ),
        )

    def collect_for_idea(self, idea_id: str, project_name: str) -> str:
        return f"Context for '{project_name}' (in-memory mode)."
