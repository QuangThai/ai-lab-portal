"""Internal link suggestion for blog drafts.

Analyzes a draft and suggests links to existing published posts
by extracting keywords and searching via the MCP search tool.
"""

from __future__ import annotations

import re
from collections import Counter

from backend.app.blog import BlogRepository
from backend.app.blog_ideas import BlogIdeaRepository
from backend.app.llm.schemas import InternalLinkSuggestion

# Words to exclude from keyword extraction
_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "need",
    "this", "that", "these", "those", "it", "its", "they", "them", "their",
    "we", "you", "he", "she", "him", "her", "his", "my", "our", "your",
    "not", "no", "nor", "so", "if", "then", "than", "too", "very", "just",
    "about", "also", "more", "most", "some", "any", "each", "every", "all",
    "both", "few", "many", "much", "such", "only", "own", "same", "other",
    "into", "over", "between", "through", "during", "before", "after",
    "above", "below", "up", "down", "out", "off", "under", "again",
    "further", "once", "here", "there", "when", "where", "why", "how",
    "what", "which", "who", "whom", "whose",
}


def _extract_keywords(text: str, max_keywords: int = 5) -> list[str]:
    """Extract the most frequent meaningful words from text."""
    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    filtered = [w for w in words if w not in _STOP_WORDS]
    counter = Counter(filtered)
    return [word for word, _ in counter.most_common(max_keywords)]


def _search_posts(keyword: str, blog_repo: BlogRepository) -> list[dict]:
    """Search published posts by keyword matching in title and excerpt."""
    results = []
    kw_lower = keyword.lower()

    for post in blog_repo.list_all():
        if post.status != "published":
            continue
        if kw_lower in post.title.lower() or kw_lower in post.slug.lower():
            results.append({
                "title": post.title,
                "slug": post.slug,
            })

    return results


def suggest_internal_links(
    idea_id: str,
    idea_repo: BlogIdeaRepository,
    blog_repo: BlogRepository,
    max_suggestions: int = 5,
) -> list[InternalLinkSuggestion]:
    """Suggest internal links for a blog idea's draft.

    Extracts keywords from the draft, searches for matching published
    posts, and returns ranked suggestions.

    Args:
        idea_id: The blog idea ID.
        idea_repo: Repository to fetch the idea.
        blog_repo: Repository to search published posts.
        max_suggestions: Maximum number of suggestions to return.

    Returns:
        A list of InternalLinkSuggestion objects.
    """
    idea = idea_repo.get_by_id(idea_id)
    if idea is None or not idea.draft_markdown:
        return []

    keywords = _extract_keywords(idea.draft_markdown)
    matched_posts: list[dict] = []
    seen_slugs: set[str] = set()

    for keyword in keywords:
        for post in _search_posts(keyword, blog_repo):
            if post["slug"] not in seen_slugs:
                matched_posts.append(post)
                seen_slugs.add(post["slug"])

    # Sort by keyword match count (posts matching more keywords appear first)
    suggestions = []
    for post in matched_posts[:max_suggestions]:
        # Find which keywords matched
        matched_kws = [
            kw for kw in keywords
            if kw in post["title"].lower() or kw in post["slug"].lower()
        ]
        reason = f"Related to: {', '.join(matched_kws[:3])}" if matched_kws else "Related content"

        suggestions.append(InternalLinkSuggestion(
            title=post["title"],
            slug=post["slug"],
            reason=reason,
        ))

    return suggestions
