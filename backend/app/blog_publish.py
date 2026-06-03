"""Bridge approved blog ideas into published blog posts."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from fastapi import HTTPException

from backend.app.blog import BlogPostCreate, BlogRepository
from backend.app.blog_ideas import BlogIdea

if TYPE_CHECKING:
    from backend.app.blog_claims import BlogClaimsRepository
    from backend.app.blog_ideas import BlogIdeaRepository

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_DEFAULT_AUTHOR = "AI Lab Team"


def slugify_title(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    if not slug:
        slug = "blog-post"
    return slug[:160]


def _existing_slugs(blog_repository: BlogRepository) -> set[str]:
    return {post.slug for post in blog_repository.list_all()}


def unique_slug(base: str, blog_repository: BlogRepository) -> str:
    taken = _existing_slugs(blog_repository)
    candidate = base
    suffix = 2
    while candidate in taken:
        stem = base[:150]
        candidate = f"{stem}-{suffix}"
        suffix += 1
    if not _SLUG_RE.match(candidate):
        raise HTTPException(status_code=400, detail="Could not derive a valid blog post slug")
    return candidate


def validate_idea_ready_to_publish(idea: BlogIdea) -> None:
    if idea.draft_status != "approved":
        raise HTTPException(
            status_code=400,
            detail="Publishing requires an approved draft",
        )
    if idea.technical_review_status != "approved":
        raise HTTPException(
            status_code=400,
            detail="Publishing requires an approved technical review",
        )
    if idea.marketing_status != "approved":
        raise HTTPException(
            status_code=400,
            detail="Publishing requires approved marketing metadata",
        )
    if not idea.draft_markdown or not idea.draft_markdown.strip():
        raise HTTPException(status_code=400, detail="Publishing requires draft markdown content")
    if not idea.marketing_metadata:
        raise HTTPException(status_code=400, detail="Publishing requires marketing metadata")


def build_blog_post_create(idea: BlogIdea, blog_repository: BlogRepository) -> BlogPostCreate:
    metadata = idea.marketing_metadata or {}
    title = (metadata.get("seo_title") or idea.title).strip()
    excerpt = (metadata.get("meta_description") or idea.article_goal).strip()
    slug_base = slugify_title(metadata.get("seo_title") or idea.title)
    slug = unique_slug(slug_base, blog_repository)
    return BlogPostCreate(
        slug=slug,
        title=title[:240],
        excerpt=excerpt,
        author_name=_DEFAULT_AUTHOR,
        content_markdown=idea.draft_markdown.strip(),
    )


def publish_idea_to_blog(
    idea_id: str,
    ideas_repository: BlogIdeaRepository,
    blog_repository: BlogRepository,
    claims_repository: BlogClaimsRepository | None = None,
) -> tuple[str, str, bool]:
    """Create and publish a blog post from an approved idea.

    Returns ``(blog_post_id, slug, already_linked)``.
    """
    idea = ideas_repository.get_by_id(idea_id)
    if idea is None:
        raise HTTPException(status_code=404, detail="Blog idea not found")

    if idea.published_blog_post_id:
        post = blog_repository.get_by_id(idea.published_blog_post_id)
        if post is not None:
            return post.id, post.slug, True
        # Stale link — allow re-publish below.

    validate_idea_ready_to_publish(idea)
    if claims_repository is not None:
        from backend.app.blog_claims import validate_claims_ready_for_publish

        validate_claims_ready_for_publish(claims_repository.list_for_idea(idea_id))
    payload = build_blog_post_create(idea, blog_repository)
    post = blog_repository.create(payload)
    published = blog_repository.publish(post.id)
    if published is None:
        raise HTTPException(status_code=500, detail="Failed to publish blog post")
    linked = ideas_repository.link_published_post(idea_id, published.id)
    if linked is None:
        raise HTTPException(status_code=404, detail="Blog idea not found")
    return published.id, published.slug, False
