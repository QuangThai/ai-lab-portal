"""GitHub release/topic ingestion for the AI News pipeline (US-xxx).

Fetches releases and trending repos from the GitHub REST API (free, 5000 req/h)
and converts them into ``ParsedFeedItem`` objects for the existing news pipeline.

Follows the same pattern as ``news_social_x_ingest.py``.

No API key needed for public data. Rate limit: 5000 requests/hour.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from backend.app.news_crawl import ParsedFeedItem

if TYPE_CHECKING:
    from backend.app.news_crawl import NewsRawItemRepository
    from backend.app.news_sources import NewsSource, NewsSourceRepository

# ─── Fixture data for tests / dev ─────────────────────────────────────────

GITHUB_FIXTURE_RELEASES: list[dict[str, Any]] = [
    {
        "repo": "openai/openai-agents-python",
        "tag_name": "v0.17.0",
        "name": "Sandbox Agents and structured output improvements",
        "body": "Added SandboxAgent with filesystem access and improved structured output handling.",
        "html_url": "https://github.com/openai/openai-agents-python/releases/tag/v0.17.0",
        "published_at": "2026-06-01T00:00:00Z",
        "stars": 8500,
        "language": "Python",
        "topics": ["ai", "agents", "sdk"],
    },
    {
        "repo": "langchain-ai/langchain",
        "tag_name": "v0.3.29",
        "name": "LangChain v0.3.29",
        "body": "New tool-calling improvements and better streaming support.",
        "html_url": "https://github.com/langchain-ai/langchain/releases/tag/v0.3.29",
        "published_at": "2026-06-02T00:00:00Z",
        "stars": 102000,
        "language": "Python",
        "topics": ["ai", "llm", "framework"],
    },
    {
        "repo": "microsoft/autogen",
        "tag_name": "v0.9.0",
        "name": "AutoGen v0.9.0: Multi-agent improvements",
        "body": "Major update with improved agent orchestration and new tool integrations.",
        "html_url": "https://github.com/microsoft/autogen/releases/tag/v0.9.0",
        "published_at": "2026-06-03T00:00:00Z",
        "stars": 35000,
        "language": "Python",
        "topics": ["ai", "agents", "multi-agent"],
    },
]


# ─── Result type ──────────────────────────────────────────────────────────


@dataclass
class GitHubIngestionResult:
    """Outcome of one GitHub source ingestion run."""

    source_id: str = ""
    releases_seen: int = 0
    items_stored: int = 0
    api_calls: int = 0
    errors: list[str] = field(default_factory=list)

    def model_dump(self) -> dict:
        return {
            "source_id": self.source_id,
            "releases_seen": self.releases_seen,
            "items_stored": self.items_stored,
            "api_calls": self.api_calls,
            "errors": self.errors,
        }


# ─── Provider ─────────────────────────────────────────────────────────────


class GitHubReleaseProvider:
    """Fetches GitHub releases for a repo.

    The real provider uses the GitHub REST API (no auth needed for public repos).
    The fake provider returns fixture data for tests/dev.
    """

    def __init__(self, *, fake: bool = True, github_token: str | None = None) -> None:
        self._fake = fake
        self._token = github_token

    def fetch_releases(self, owner: str, repo: str) -> list[dict[str, Any]]:
        """Fetch releases for a GitHub repository.

        Args:
            owner: Repository owner (e.g. ``"openai"``).
            repo: Repository name (e.g. ``"openai-agents-python"``).

        Returns:
            List of release dicts with keys:
            ``tag_name``, ``name``, ``body``, ``html_url``, ``published_at``.
        """
        if self._fake:
            return self._fake_releases(owner, repo)

        import urllib.request

        url = f"https://api.github.com/repos/{owner}/{repo}/releases?per_page=10"
        headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "ai-lab-portal/1.0"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data: list[dict[str, Any]] = json.loads(resp.read().decode())
            return [
                {
                    "repo": f"{owner}/{repo}",
                    "tag_name": r.get("tag_name", ""),
                    "name": r.get("name", "") or r.get("tag_name", ""),
                    "body": (r.get("body") or "")[:2000],
                    "html_url": r.get("html_url", ""),
                    "published_at": r.get("published_at", ""),
                }
                for r in data
            ]

    def _fake_releases(self, owner: str, repo: str) -> list[dict[str, Any]]:
        repo_path = f"{owner}/{repo}"
        return [r for r in GITHUB_FIXTURE_RELEASES if r["repo"] == repo_path] or [
            {
                "repo": repo_path,
                "tag_name": "v1.0.0",
                "name": "Initial release",
                "body": "First stable release with core functionality.",
                "html_url": f"https://github.com/{repo_path}/releases/tag/v1.0.0",
                "published_at": "2026-01-15T00:00:00Z",
            }
        ]


# ─── Converters ───────────────────────────────────────────────────────────


def _release_to_raw_item(
    release: dict[str, Any],
    *,
    source_id: str,
    fetched_at: datetime,
) -> ParsedFeedItem:
    """Convert a GitHub release dict to a ParsedFeedItem.

    The url_or_identifier format is ``owner/repo`` (e.g. ``openai/openai-cookbook``).
    """
    repo_path = release.get("repo", "")
    tag = release.get("tag_name", "")
    external_id = f"github_release_{repo_path}_{tag}" if tag else f"github_release_{repo_path}_{uuid4().hex[:12]}"

    title = release.get("name", "")[:240] or f"Release {tag}"
    link_url = release.get("html_url", f"https://github.com/{repo_path}/releases")

    published_at = None
    if release.get("published_at"):
        try:
            published_at = datetime.fromisoformat(release["published_at"].replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass

    return ParsedFeedItem(
        external_id=external_id,
        title=title,
        link_url=link_url,
        published_at=published_at,
        raw_payload={
            "github_repo": repo_path,
            "github_tag": tag,
            "github_release_name": release.get("name", ""),
            "github_body_preview": (release.get("body", "") or "")[:500],
            "github_stars": release.get("stars"),
            "github_language": release.get("language"),
            "github_topics": release.get("topics", []),
            "source_type": "github",
        },
    )


# ─── Ingestion ────────────────────────────────────────────────────────────


def _parse_repo_path(url_or_identifier: str) -> tuple[str, str]:
    """Parse ``owner/repo`` from a GitHub URL or identifier.

    Handles:
    - ``openai/openai-cookbook``
    - ``https://github.com/openai/openai-cookbook``
    - ``https://github.com/openai/openai-cookbook/releases``
    """
    path = url_or_identifier.strip()
    if "github.com/" in path:
        path = path.split("github.com/", 1)[1]
    path = path.split("/releases")[0].split("/tags")[0].rstrip("/")
    parts = path.split("/")
    if len(parts) >= 2:
        return parts[0], parts[1]
    return parts[0], ""


def run_github_fetch(
    source_id: str,
    *,
    sources: NewsSourceRepository,
    raw_items: NewsRawItemRepository,
    provider: GitHubReleaseProvider | None = None,
) -> GitHubIngestionResult:
    """Fetch releases for one GitHub source and store as raw items.

    Args:
        source_id: The news source ID to fetch.
        sources: NewsSourceRepository for source config lookup.
        raw_items: NewsRawItemRepository for storing fetched raw items.
        provider: Optional GitHubReleaseProvider (uses fake by default).

    Returns:
        GitHubIngestionResult with counts.
    """
    source = sources.get_by_id(source_id)
    if source is None:
        raise ValueError(f"GitHub source not found: {source_id}")
    if source.source_type != "github":
        raise ValueError(f"Source {source_id} is not a github source (type={source.source_type})")
    if not source.is_enabled:
        raise ValueError(f"Source {source_id} is disabled")

    owner, repo = _parse_repo_path(source.url_or_identifier)
    if not owner or not repo:
        raise ValueError(f"Invalid GitHub identifier: {source.url_or_identifier}")

    fetcher = provider or GitHubReleaseProvider()
    releases = fetcher.fetch_releases(owner, repo)
    fetched_at = datetime.now(UTC)

    result = GitHubIngestionResult(
        source_id=source_id,
        releases_seen=len(releases),
        api_calls=1,
    )

    for release in releases:
        tag = release.get("tag_name", "")
        repo_path = release.get("repo", f"{owner}/{repo}")
        external_id = f"github_release_{repo_path}_{tag}" if tag else f"github_release_{repo_path}_{uuid4().hex[:12]}"

        feed_item = _release_to_raw_item(
            release,
            source_id=source_id,
            fetched_at=fetched_at,
        )

        content_hash = feed_item.external_id
        if raw_items.upsert_item(
            source_id=source_id,
            item=feed_item,
            content_hash=content_hash,
            fetched_at=fetched_at,
        ):
            result.items_stored += 1

    sources.touch_last_crawled(source_id, fetched_at)
    return result


def run_due_github_sources(
    *,
    sources: NewsSourceRepository,
    raw_items: NewsRawItemRepository,
    provider: GitHubReleaseProvider | None = None,
) -> list[GitHubIngestionResult]:
    """Fetch all due github sources."""
    from datetime import timedelta

    now = datetime.now(UTC)
    results: list[GitHubIngestionResult] = []

    for source in sources.list_all():
        src = sources.get_by_id(source.id)
        if not src or not src.is_enabled or src.source_type != "github":
            continue
        if src.last_crawled_at is not None:
            if src.last_crawled_at + timedelta(minutes=src.crawl_frequency_minutes) > now:
                continue
        try:
            results.append(
                run_github_fetch(
                    src.id,
                    sources=sources,
                    raw_items=raw_items,
                    provider=provider,
                )
            )
        except ValueError as exc:
            result = GitHubIngestionResult(source_id=src.id, errors=[str(exc)])
            results.append(result)

    return results
