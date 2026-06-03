import json
from time import time

from fastapi.testclient import TestClient

from backend.app.admin_boundary import ADMIN_IDENTITY_HEADER, ADMIN_SIGNATURE_HEADER, sign_admin_identity
from backend.app.main import create_app
from backend.app.settings import Settings
from backend.app.showcase import ShowcaseRepository

TEST_SECRET = "test-admin-boundary-secret-at-least-32-chars"


def _client(repository: ShowcaseRepository | None = None) -> TestClient:
    return TestClient(
        create_app(
            Settings(environment="test", admin_boundary_secret=TEST_SECRET),
            showcase_repository=repository or ShowcaseRepository(items=[]),
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


def _create_payload(slug: str = "new-ai-lab-showcase") -> dict[str, str]:
    return {
        "slug": slug,
        "title": "New AI Lab Showcase",
        "hero_summary": "A draft showcase created from the admin API.",
        "industry": "Engineering",
        "use_case": "Workflow design",
        "content_markdown": "Draft showcase content for human review.",
    }


def test_admin_showcase_list_requires_identity() -> None:
    response = _client().get("/admin/showcases")

    assert response.status_code == 401


def test_admin_showcase_list_returns_items_for_admin() -> None:
    client = _client()
    create_response = client.post("/admin/showcases", json=_create_payload(), headers=_admin_headers())

    response = client.get("/admin/showcases", headers=_admin_headers())

    assert response.status_code == 200
    assert response.json()[0]["id"] == create_response.json()["id"]
    assert response.json()[0]["status"] == "draft"


def test_admin_showcase_create_and_publish() -> None:
    client = _client()
    create_response = client.post("/admin/showcases", json=_create_payload(), headers=_admin_headers())
    showcase_id = create_response.json()["id"]

    publish_response = client.post(f"/admin/showcases/{showcase_id}/publish", headers=_admin_headers())

    assert publish_response.status_code == 200
    assert publish_response.json()["status"] == "published"
    assert publish_response.json()["published_at"] is not None

    public_response = client.get("/public/showcases/new-ai-lab-showcase")
    assert public_response.status_code == 200
