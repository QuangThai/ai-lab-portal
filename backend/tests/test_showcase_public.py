from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.settings import Settings


def test_public_showcase_list_returns_only_published_items() -> None:
    client = TestClient(create_app(Settings(environment="test")))

    response = client.get("/public/showcases")

    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2
    slugs = {item["slug"] for item in items}
    assert "scopelytics" in slugs
    assert "ai-interview-system" in slugs
    assert "draft-internal-assistant" not in slugs


def test_public_showcase_detail_returns_published_item() -> None:
    client = TestClient(create_app(Settings(environment="test")))

    response = client.get("/public/showcases/scopelytics")

    assert response.status_code == 200
    assert response.json()["title"] == "Scopelytics"
    assert "human" in response.json()["content_markdown"].lower()


def test_public_showcase_detail_rejects_draft_or_missing_items() -> None:
    client = TestClient(create_app(Settings(environment="test")))

    draft_response = client.get("/public/showcases/draft-internal-assistant")
    missing_response = client.get("/public/showcases/not-found")

    assert draft_response.status_code == 404
    assert missing_response.status_code == 404
