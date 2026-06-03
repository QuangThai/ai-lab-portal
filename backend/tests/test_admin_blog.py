import json
from time import time

from fastapi.testclient import TestClient

from backend.app.admin_boundary import ADMIN_IDENTITY_HEADER, ADMIN_SIGNATURE_HEADER, sign_admin_identity
from backend.app.blog import BlogRepository
from backend.app.main import create_app
from backend.app.settings import Settings

TEST_SECRET = "test-admin-boundary-secret-at-least-32-chars"


def _client(repository: BlogRepository | None = None) -> TestClient:
    return TestClient(
        create_app(
            Settings(environment="test", admin_boundary_secret=TEST_SECRET),
            blog_repository=repository or BlogRepository(posts=[]),
        )
    )


def _admin_headers() -> dict[str, str]:
    payload = json.dumps(
        {
            "user_id": "user_123",
            "email": "admin@example.com",
            "role": "admin",
            "issued_at": int(time()),
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return {
        ADMIN_IDENTITY_HEADER: payload,
        ADMIN_SIGNATURE_HEADER: sign_admin_identity(payload, TEST_SECRET),
    }


def _create_payload(slug: str = "new-ai-lab-post") -> dict[str, str]:
    return {
        "slug": slug,
        "title": "New AI Lab Post",
        "excerpt": "A draft post created from the admin API.",
        "author_name": "AI Lab Team",
        "content_markdown": "Draft content for human review.",
    }


def test_admin_blog_list_requires_identity() -> None:
    response = _client().get("/admin/blog-posts")

    assert response.status_code == 401


def test_admin_blog_list_returns_posts_for_admin() -> None:
    client = _client()
    create_response = client.post("/admin/blog-posts", json=_create_payload(), headers=_admin_headers())

    response = client.get("/admin/blog-posts", headers=_admin_headers())

    assert response.status_code == 200
    assert response.json()[0]["id"] == create_response.json()["id"]
    assert response.json()[0]["status"] == "draft"


def test_admin_blog_detail_returns_post_for_admin() -> None:
    client = _client()
    create_response = client.post("/admin/blog-posts", json=_create_payload(), headers=_admin_headers())

    response = client.get(f"/admin/blog-posts/{create_response.json()['id']}", headers=_admin_headers())

    assert response.status_code == 200
    assert response.json()["slug"] == "new-ai-lab-post"
    assert response.json()["content_markdown"] == "Draft content for human review."


def test_admin_blog_create_requires_identity() -> None:
    response = _client().post("/admin/blog-posts", json=_create_payload())

    assert response.status_code == 401


def test_admin_can_create_update_publish_and_unpublish_blog_post_with_audit() -> None:
    repository = BlogRepository(posts=[])
    client = _client(repository)

    create_response = client.post("/admin/blog-posts", json=_create_payload(), headers=_admin_headers())

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["status"] == "draft"
    assert created["published_at"] is None

    public_draft_response = client.get("/public/blog-posts/new-ai-lab-post")
    assert public_draft_response.status_code == 404

    update_response = client.patch(
        f"/admin/blog-posts/{created['id']}",
        json={"title": "Updated AI Lab Post"},
        headers=_admin_headers(),
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Updated AI Lab Post"

    publish_response = client.post(f"/admin/blog-posts/{created['id']}/publish", headers=_admin_headers())
    assert publish_response.status_code == 200
    assert publish_response.json()["status"] == "published"
    assert publish_response.json()["published_at"] is not None

    public_response = client.get("/public/blog-posts/new-ai-lab-post")
    assert public_response.status_code == 200
    assert public_response.json()["title"] == "Updated AI Lab Post"

    unpublish_response = client.post(f"/admin/blog-posts/{created['id']}/unpublish", headers=_admin_headers())
    assert unpublish_response.status_code == 200
    assert unpublish_response.json()["status"] == "draft"

    hidden_response = client.get("/public/blog-posts/new-ai-lab-post")
    assert hidden_response.status_code == 404

    audit_response = client.get("/admin/audit-events", headers=_admin_headers())
    assert audit_response.status_code == 200
    assert [event["action"] for event in audit_response.json()] == [
        "blog_post.created",
        "blog_post.updated",
        "blog_post.published",
        "blog_post.unpublished",
    ]
    assert {event["actor_email"] for event in audit_response.json()} == {"admin@example.com"}


def test_admin_blog_mutations_return_404_for_missing_posts() -> None:
    client = _client()

    update_response = client.patch("/admin/blog-posts/missing", json={"title": "Missing"}, headers=_admin_headers())
    publish_response = client.post("/admin/blog-posts/missing/publish", headers=_admin_headers())

    assert update_response.status_code == 404
    assert publish_response.status_code == 404
