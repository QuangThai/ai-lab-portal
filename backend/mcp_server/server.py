"""FastMCP server exposing AI Lab Portal tools for Agents SDK agents.

Run via stdio (for integration with Agents SDK MCPServerStdio)::

    python -m backend.mcp_server.server

Or via SSE (for standalone HTTP access)::

    python -m backend.mcp_server.server --transport sse --port 9000

Tools:
- ``blog_agent__idea_context`` — Get project context for a blog idea
- ``blog_agent__idea_status`` — Get pipeline status for a blog idea (DB-backed)
- ``blog_agent__search_posts`` — Search published blog posts by keyword (DB-backed)
"""

from __future__ import annotations

import argparse
import os
from typing import Any

from mcp.server.fastmcp import FastMCP
from sqlalchemy import select, text

# Lazy globals — initialised once on first tool call
_engine: Any = None
_IN_MEMORY_FALLBACK = False


def _get_engine():
    """Create (or return) a database engine from settings.

    Once connectivity fails the flag is permanently set so that
    subsequent calls return ``None`` immediately without retrying.
    """
    global _engine, _IN_MEMORY_FALLBACK
    if _engine is not None:
        return _engine
    if _IN_MEMORY_FALLBACK:
        return None

    try:
        from backend.app.settings import get_settings
        from sqlalchemy import create_engine

        url = os.environ.get("AI_LAB_DATABASE_URL") or str(get_settings().database_url)
        candidate = create_engine(
            url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 2},
        )

        # Quick connectivity check
        with candidate.connect() as conn:
            conn.execute(text("SELECT 1"))

        _engine = candidate
        _IN_MEMORY_FALLBACK = False
        return _engine
    except Exception as exc:
        import sys as _sys

        print(
            f"[mcp-server] DB unavailable, using in-memory fallback: {exc}",
            file=_sys.stderr,
        )
        _engine = None
        _IN_MEMORY_FALLBACK = True
        return None


# Create the MCP server instance (port is set here, not in mcp.run())
mcp = FastMCP(
    "ai-lab-portal",
    instructions=(
        "AI Lab Portal internal tools. Use these to query project context, "
        "check idea pipeline status, and search published content during "
        "blog idea generation and review."
    ),
    host="127.0.0.1",
    port=9000,
)

# ── In-memory data stores (fallback for test/dev without Postgres) ──

_PROJECT_CONTEXTS: dict[str, dict[str, str]] = {
    "default": {
        "name": "Scopelytics",
        "summary": "An AI-powered business analysis tool that helps companies "
        "understand their competitive landscape through automated data collection "
        "and intelligent reporting.",
        "capabilities": "LLM-based analysis, automated data collection, "
        "competitive intelligence dashboards, custom report generation",
        "highlights": "Built with Python/FastAPI backend, Next.js frontend, "
        "PostgreSQL for structured data, Redis for caching",
        "value": "Reduces manual competitive analysis time by 80%",
    },
}

_IDEAS: dict[str, dict[str, Any]] = {}


def _mem_get_or_create_idea(idea_id: str) -> dict[str, Any]:
    """Get or create an idea entry in the in-memory store."""
    if idea_id not in _IDEAS:
        _IDEAS[idea_id] = {
            "id": idea_id,
            "status": "idea",
            "title": "",
            "outline_status": None,
            "draft_status": None,
            "review_status": None,
            "marketing_status": None,
        }
    return _IDEAS[idea_id]


# ── DB-backed helpers ────────────────────────────────────────────────


def _db_get_idea_status(idea_id: str) -> str:
    """Query blog_ideas table for pipeline status."""
    engine = _get_engine()
    if engine is None:
        # Fall back to in-memory
        return _mem_get_idea_status(idea_id)

    table = _resolve_table("blog_ideas")
    if table is None:
        return _mem_get_idea_status(idea_id)

    try:
        with engine.connect() as conn:
            row = conn.execute(
                select(
                    table.c.id,
                    table.c.title,
                    table.c.status,
                    table.c.outline_status,
                    table.c.draft_status,
                    table.c.technical_review_status,
                    table.c.marketing_status,
                    table.c.published_blog_post_id,
                ).where(table.c.id == idea_id)
            ).mappings().first()

        if row is None:
            return f"Idea '{idea_id}' not found."

        lines = [f"Idea: {row['id']}"]
        if row.get("title"):
            lines.append(f"Title: {row['title']}")
        lines.append(f"Status: {row['status']}")

        stages = {
            "Outline": row.get("outline_status"),
            "Draft": row.get("draft_status"),
            "Review": row.get("technical_review_status"),
            "Marketing": row.get("marketing_status"),
        }
        for stage, status in stages.items():
            lines.append(f"{stage}: {status or 'not started'}")

        if row.get("published_blog_post_id"):
            lines.append(f"Published post ID: {row['published_blog_post_id']}")

        return "\n".join(lines)
    except Exception as exc:
        return f"Error querying idea '{idea_id}': {exc}"


def _mem_get_idea_status(idea_id: str) -> str:
    """In-memory fallback for idea status."""
    idea = _mem_get_or_create_idea(idea_id)
    lines = [f"Idea: {idea['id']}"]
    lines.append(f"Status: {idea['status']}")

    if idea.get("title"):
        lines.append(f"Title: {idea['title']}")

    stage_info = {
        "outline": idea.get("outline_status"),
        "draft": idea.get("draft_status"),
        "review": idea.get("review_status"),
        "marketing": idea.get("marketing_status"),
    }
    for stage, status in stage_info.items():
        lines.append(f"{stage.capitalize()}: {status or 'not started'}")

    return "\n".join(lines)


def _db_search_posts(query: str, max_results: int = 5) -> str:
    """Search published blog posts via database."""
    engine = _get_engine()
    if engine is None:
        return _mem_search_posts(query, max_results)

    table = _resolve_table("blog_posts")
    if table is None:
        return _mem_search_posts(query, max_results)

    try:
        pattern = f"%{query}%"
        with engine.connect() as conn:
            rows = conn.execute(
                select(
                    table.c.id,
                    table.c.title,
                    table.c.excerpt,
                ).where(
                    table.c.status == "published"
                ).where(
                    table.c.title.ilike(pattern) | table.c.excerpt.ilike(pattern) | table.c.content_markdown.ilike(pattern)
                ).limit(max_results)
            ).mappings().all()

        if not rows:
            return f"No published posts found matching '{query}'."

        lines = [f"Found {len(rows)} published post(s) matching '{query}':\n"]
        for i, row in enumerate(rows, 1):
            lines.append(f"{i}. {row['title']}")
            excerpt = (row.get("excerpt") or "")[:120]
            if excerpt:
                lines.append(f"   {excerpt}")
            lines.append("")

        return "\n".join(lines).strip()
    except Exception as exc:
        return f"Error searching posts: {exc}"


def _mem_search_posts(query: str, max_results: int = 5) -> str:
    """In-memory fallback for post search."""
    _posts: list[dict[str, str]] = [
        {
            "title": "Building AI-Powered Competitive Intelligence Dashboards",
            "summary": "How Scopelytics uses LLMs to automate competitive analysis",
            "tags": "AI, competitive-intelligence, dashboards",
        },
        {
            "title": "FastAPI + Next.js: A Modern Full-Stack Architecture",
            "summary": "Why we chose Python/FastAPI and Next.js for our platform",
            "tags": "architecture, fastapi, nextjs",
        },
        {
            "title": "Automated Data Collection at Scale",
            "summary": "How Scopelytics collects and processes competitive data",
            "tags": "data-collection, automation, scale",
        },
    ]

    query_lower = query.lower()
    results = [
        p
        for p in _posts
        if query_lower in p["title"].lower()
        or query_lower in p["summary"].lower()
        or query_lower in p["tags"].lower()
    ][:max_results]

    if not results:
        return f"No posts found matching '{query}'."

    lines = [f"Found {len(results)} post(s) matching '{query}':\n"]
    for i, post in enumerate(results, 1):
        lines.append(f"{i}. {post['title']}")
        lines.append(f"   {post['summary']}")
        lines.append("")

    return "\n".join(lines).strip()


_resolved_tables: dict[str, Any] = {}


def _resolve_table(name: str) -> Any:
    """Resolve a SQLAlchemy Table by name from the metadata."""
    if name in _resolved_tables:
        return _resolved_tables[name]
    try:
        from backend.app.database import metadata

        table = metadata.tables.get(name)
        _resolved_tables[name] = table
        return table
    except Exception:
        return None


# ── Tools ──────────────────────────────────────────────────────────────


@mcp.tool(
    name="blog_agent__idea_context",
    description=(
        "Get project context information for a blog idea. "
        "Returns the project name, summary, AI capabilities, "
        "technical highlights, and business value."
    ),
)
def get_project_context(project_name: str = "default") -> str:
    """Get the project context for generating a blog idea.

    Queries the projects database table for real project data.
    Falls back to hardcoded fixture data if the DB is unavailable.

    Args:
        project_name: The project name or "default" for the main project.

    Returns:
        A formatted string with project context details.
    """
    # Try real DB first
    if not _IN_MEMORY_FALLBACK and _engine is not None:
        try:
            from backend.app.database import projects as projects_table

            with _engine.begin() as conn:
                row = conn.execute(
                    select(
                        projects_table.c.title,
                        projects_table.c.description,
                        projects_table.c.content_markdown,
                    )
                    .where(projects_table.c.title.ilike(f"%{project_name}%"))
                    .limit(1)
                ).mappings().first()
                if row:
                    return (
                        f"Project: {row['title']}\n"
                        f"Summary: {row['description'] or ''}\n"
                        f"Content:\n{(row['content_markdown'] or '')[:2000]}"
                    )
        except Exception:
            pass

    # Fallback to hardcoded fixture
    ctx = _PROJECT_CONTEXTS.get(project_name)
    if ctx is None:
        return f"Unknown project: {project_name}"

    return (
        f"Project: {ctx['name']}\n"
        f"Summary: {ctx['summary']}\n"
        f"AI Capabilities: {ctx['capabilities']}\n"
        f"Technical Highlights: {ctx['highlights']}\n"
        f"Business Value: {ctx['value']}"
    )


@mcp.tool(
    name="blog_agent__idea_status",
    description=(
        "Get the current pipeline status for a blog idea. "
        "Returns the stage (idea/outline/draft/review/marketing/published) "
        "and approval status of each stage. Queries the database."
    ),
)
def get_idea_status(idea_id: str) -> str:
    """Get the pipeline status of a blog idea.

    Queries the blog_ideas table. Falls back to in-memory data when the
    database is unavailable (e.g., during tests).

    Args:
        idea_id: The blog idea ID.

    Returns:
        A formatted string with the current pipeline status.
    """
    return _db_get_idea_status(idea_id)


@mcp.tool(
    name="blog_agent__search_posts",
    description=(
        "Search published blog posts by keyword. "
        "Returns matching post titles and summaries (excerpts). "
        "Use this to avoid duplicating existing content. "
        "Queries the database for published blog posts."
    ),
)
def search_posts(query: str, max_results: int = 5) -> str:
    """Search published blog posts by keyword.

    Queries the blog_posts table. Falls back to in-memory data when the
    database is unavailable (e.g., during tests).

    Args:
        query: The search query string.
        max_results: Maximum number of results to return (default 5).

    Returns:
        A formatted string with matching post titles and excerpts.
    """
    return _db_search_posts(query, max_results)


# ── News tools ──────────────────────────────────────────────────────────


@mcp.tool(
    name="news__source_reliability",
    description=(
        "Get the reliability / credibility score for a news source. "
        "Use this to check whether an article comes from a trusted source "
        "before scoring or publishing. Queries the news_sources table."
    ),
)
def get_source_reliability(source_name: str) -> str:
    """Get the reliability score of a news source by name.

    Queries the news_sources table. Falls back to in-memory data when
    the database is unavailable.

    Args:
        source_name: The news source name (e.g. "OpenAI Blog").

    Returns:
        A formatted string with source reliability information.
    """
    try:
        engine = _get_engine()
        if engine is None:
            raise RuntimeError("no engine")

        table = _resolve_table("news_sources")
        if table is None:
            return f"Source table not available. Configured sources would be checked for '{source_name}'."

        from sqlalchemy import select

        with engine.connect() as conn:
            stmt = select(table).where(table.c.name.ilike(f"%{source_name}%"))
            row = conn.execute(stmt).fetchone()

        if row is None:
            # Return a message about unknown source
            return (
                f"Source '{source_name}' not found in the database.\n"
                f"Default credibility score: 0.5 (neutral)\n"
                f"Recommendation: Check the source URL manually before publishing."
            )

        row_dict = dict(row._mapping)
        score = row_dict.get("credibility_base_score", row_dict.get("credibility_score", "N/A"))
        return (
            f"Source: {row_dict.get('name', source_name)}\n"
            f"ID: {row_dict.get('id', 'N/A')}\n"
            f"Credibility score: {score}\n"
            f"URL: {row_dict.get('url_or_identifier', 'N/A')}\n"
            f"Description: {row_dict.get('description', 'N/A')}"
        )
    except Exception:
        return (
            f"Source reliability for '{source_name}': 0.5 (neutral, database unavailable).\n"
            f"Tip: Known sources include 'OpenAI Blog', 'Anthropic Blog', and 'TechCrunch'."
        )


@mcp.tool(
    name="news__trending_topics",
    description=(
        "Get trending or recent topics from published blog posts. "
        "Use this to understand what topics are currently popular "
        "when evaluating news articles for relevance. "
        "Queries the blog_posts table for recent post topics."
    ),
)
def get_trending_topics(days: int = 7, max_topics: int = 10) -> str:
    """Get trending topics from recently published blog posts.

    Args:
        days: Look back window in days (default 7).
        max_topics: Maximum number of topics to return (default 10).

    Returns:
        A formatted string with trending topics.
    """
    try:
        engine = _get_engine()
        if engine is None:
            raise RuntimeError("no engine")

        table = _resolve_table("blog_posts")
        if table is None:
            return f"Blog posts table not available. Cannot determine trending topics."

        from datetime import datetime, timezone
        from sqlalchemy import func, select

        cutoff = datetime.now(timezone.utc)

        with engine.connect() as conn:
            stmt = (
                select(table.c.tags, table.c.title)
                .where(table.c.published_at >= cutoff)
                .limit(50)
            )
            rows = conn.execute(stmt).fetchall()

        if not rows:
            return f"No recent posts found in the last {days} days."

        # Collect and count tags
        tag_counts: dict[str, int] = {}
        titles: list[str] = []
        for row in rows:
            row_dict = dict(row._mapping)
            titles.append(str(row_dict.get("title", "")))
            tags_raw = row_dict.get("tags", [])
            if isinstance(tags_raw, str):
                try:
                    import json as _json

                    tags_raw = _json.loads(tags_raw)
                except Exception:
                    tags_raw = [tags_raw]
            for tag in tags_raw:
                tag_counts[str(tag).strip().lower()] = (
                    tag_counts.get(str(tag).strip().lower(), 0) + 1
                )

        # Also extract keywords from titles
        for title in titles:
            for word in title.split():
                word = word.strip(".,!?:;\"'()[]").lower()
                if len(word) > 3 and word not in ("the", "and", "for", "that", "this", "with", "from", "your"):
                    tag_counts[word] = tag_counts.get(word, 0) + 1

        sorted_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:max_topics]

        lines = [f"Trending topics (last {days}d):"]
        for tag, count in sorted_tags:
            lines.append(f"  - {tag}: {count} occurrences")

        return "\n".join(lines)

    except Exception as exc:
        return f"Trending topics: Unable to query. Error: {exc}"


@mcp.tool(
    name="news__article_context",
    description=(
        "Get context about a news article from the extraction pipeline. "
        "Returns title, source, publication date, and content excerpt. "
        "Use this during scoring to understand an article's background. "
        "Queries the extracted_articles table."
    ),
)
def get_article_context(article_id: str) -> str:
    """Get context for an extracted article by ID.

    Args:
        article_id: The extracted article ID.

    Returns:
        A formatted string with article context information.
    """
    try:
        engine = _get_engine()
        if engine is None:
            raise RuntimeError("no engine")

        table = _resolve_table("extracted_articles")
        if table is None:
            return f"Article context: Extracted articles table not available."

        from sqlalchemy import select

        with engine.connect() as conn:
            stmt = select(table).where(table.c.id == article_id)
            row = conn.execute(stmt).fetchone()

        if row is None:
            return f"Article '{article_id}' not found."

        row_dict = dict(row._mapping)
        content = str(row_dict.get("content_text", "") or "")
        excerpt = content[:500] + "..." if len(content) > 500 else content

        return (
            f"Title: {row_dict.get('title', 'N/A')}\n"
            f"Source URL: {row_dict.get('source_url', 'N/A')}\n"
            f"Published: {row_dict.get('published_at', 'N/A')}\n"
            f"Author: {row_dict.get('author', 'N/A')}\n"
            f"Site: {row_dict.get('site_name', 'N/A')}\n"
            f"Content excerpt:\n{excerpt}"
        )
    except Exception:
        return f"Article context: Unable to query for '{article_id}'. Database may be unavailable."


# ── CLI entry point ────────────────────────────────────────────────────


def main() -> None:
    """Run the MCP server."""
    parser = argparse.ArgumentParser(description="AI Lab Portal MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9000,
        help="Port for SSE transport (default: 9000)",
    )
    args = parser.parse_args()

    # Update port from CLI args (FastMCP.run() does not accept port,
    # so it must be set on the instance before calling run)
    if args.transport != "stdio":
        mcp.settings.port = args.port
        mcp.run(transport=args.transport)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
