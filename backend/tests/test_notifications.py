"""Tests for notifications (US-064)."""

from __future__ import annotations

import json
from time import time

from fastapi.testclient import TestClient

from backend.app.admin_boundary import (
    USER_IDENTITY_HEADER,
    USER_SIGNATURE_HEADER,
    sign_admin_identity,
)
from backend.app.main import create_app
from backend.app.notifications import (
    InMemoryNotificationRepository,
)
from backend.app.settings import Settings


TEST_SECRET = Settings(environment="test").admin_boundary_secret.get_secret_value()


def _user_headers(user_id: str = "user-1", email: str = "user@test.com") -> dict[str, str]:
    now = int(time())
    identity = {"user_id": user_id, "email": email, "role": "user", "issued_at": now}
    payload = json.dumps(identity)
    return {
        USER_IDENTITY_HEADER: payload,
        USER_SIGNATURE_HEADER: sign_admin_identity(payload, TEST_SECRET),
    }


# --- Unit: InMemoryNotificationRepository ---

def test_create_notification() -> None:
    repo = InMemoryNotificationRepository()
    notif = repo.create(
        user_id="user-2",
        type="follow",
        actor_user_id="user-1",
        actor_email="user1@test.com",
        actor_display_name="User One",
        resource_id="user-1",
        resource_type="user",
        preview="",
        group_key="follow:user-1",
        link="/profile/user-1",
    )
    assert notif.user_id == "user-2"
    assert notif.type == "follow"
    assert notif.actor_user_id == "user-1"
    assert notif.read is False
    assert notif.id.startswith("notif_")
    assert notif.actor_display_name == "User One"
    assert notif.preview == ""
    assert notif.group_key == "follow:user-1"
    assert notif.link == "/profile/user-1"


def test_list_for_user() -> None:
    repo = InMemoryNotificationRepository()
    repo.create(user_id="user-2", type="follow", actor_user_id="user-1", resource_id="user-1", resource_type="user")
    repo.create(user_id="user-2", type="comment_reply", actor_user_id="user-1", resource_id="post-1", resource_type="post")
    repo.create(user_id="user-3", type="follow", actor_user_id="user-1", resource_id="user-1", resource_type="user")

    user2_notifs = repo.list_for_user("user-2")
    assert len(user2_notifs) == 2
    assert all(n.type in ("follow", "comment_reply") for n in user2_notifs)
    assert all(n.id.startswith("notif_") for n in user2_notifs)

    user3_notifs = repo.list_for_user("user-3")
    assert len(user3_notifs) == 1


def test_unread_count() -> None:
    repo = InMemoryNotificationRepository()
    repo.create(user_id="user-1", type="follow", actor_user_id="user-2", resource_id="user-2", resource_type="user")
    repo.create(user_id="user-1", type="follow", actor_user_id="user-3", resource_id="user-3", resource_type="user")
    assert repo.unread_count("user-1") == 2
    assert repo.unread_count("user-2") == 0


def test_mark_read() -> None:
    repo = InMemoryNotificationRepository()
    notif = repo.create(user_id="user-1", type="follow", actor_user_id="user-2", resource_id="user-2", resource_type="user")
    assert repo.unread_count("user-1") == 1

    marked = repo.mark_read(notif.id, "user-1")
    assert marked is not None
    assert marked.read is True
    assert repo.unread_count("user-1") == 0


def test_mark_read_not_found() -> None:
    repo = InMemoryNotificationRepository()
    assert repo.mark_read("nonexistent", "user-1") is None


def test_mark_read_wrong_user() -> None:
    repo = InMemoryNotificationRepository()
    notif = repo.create(user_id="user-1", type="follow", actor_user_id="user-2", resource_id="user-2", resource_type="user")
    assert repo.mark_read(notif.id, "user-2") is None
    assert repo.unread_count("user-1") == 1


def test_mark_all_read() -> None:
    repo = InMemoryNotificationRepository()
    repo.create(user_id="user-1", type="follow", actor_user_id="user-2", resource_id="user-2", resource_type="user")
    repo.create(user_id="user-1", type="comment_reply", actor_user_id="user-3", resource_id="post-1", resource_type="post")
    repo.create(user_id="user-2", type="follow", actor_user_id="user-1", resource_id="user-1", resource_type="user")

    count = repo.mark_all_read("user-1")
    assert count == 2
    assert repo.unread_count("user-1") == 0
    assert repo.unread_count("user-2") == 1  # user-2's notif should still be unread


def test_list_limit() -> None:
    repo = InMemoryNotificationRepository()
    for i in range(25):
        repo.create(
            user_id="user-1",
            type="follow",
            actor_user_id=f"actor-{i}",
            resource_id=f"actor-{i}",
            resource_type="user",
        )
    notifs = repo.list_for_user("user-1", limit=10)
    assert len(notifs) == 10


def test_list_offset() -> None:
    repo = InMemoryNotificationRepository()
    for i in range(10):
        repo.create(
            user_id="user-1",
            type="follow",
            actor_user_id=f"actor-{i}",
            resource_id=f"actor-{i}",
            resource_type="user",
        )
    # First 5 (desc by created_at, but same timestamp so any order)
    first_page = repo.list_for_user("user-1", limit=5, offset=0)
    assert len(first_page) == 5
    # Next 5 should be different from first
    second_page = repo.list_for_user("user-1", limit=5, offset=5)
    assert len(second_page) == 5
    first_ids = {n.id for n in first_page}
    second_ids = {n.id for n in second_page}
    # No overlap between pages
    assert first_ids.isdisjoint(second_ids)
    # Total should be 10
    assert len(first_ids | second_ids) == 10


# --- API: notification routes ---

def _make_app():
    notif_repo = InMemoryNotificationRepository()
    app = create_app(notification_repository=notif_repo)
    return TestClient(app), notif_repo


def test_api_list_notifications() -> None:
    client, repo = _make_app()
    repo.create(user_id="user-1", type="follow", actor_user_id="user-2", resource_id="user-2", resource_type="user")

    resp = client.get("/public/notifications", headers=_user_headers("user-1"))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["type"] == "follow"


def test_api_list_notifications_requires_auth() -> None:
    client, _ = _make_app()
    resp = client.get("/public/notifications")
    assert resp.status_code == 401


def test_api_unread_count() -> None:
    client, repo = _make_app()
    repo.create(user_id="user-1", type="follow", actor_user_id="user-2", resource_id="user-2", resource_type="user")
    repo.create(user_id="user-1", type="follow", actor_user_id="user-3", resource_id="user-3", resource_type="user")

    resp = client.get("/public/notifications/unread-count", headers=_user_headers("user-1"))
    assert resp.status_code == 200
    assert resp.json()["count"] == 2


def test_api_mark_read() -> None:
    client, repo = _make_app()
    notif = repo.create(user_id="user-1", type="follow", actor_user_id="user-2", resource_id="user-2", resource_type="user")

    resp = client.post(f"/public/notifications/{notif.id}/read", headers=_user_headers("user-1"))
    assert resp.status_code == 200
    assert resp.json()["status"] == "read"

    # Verify unread count decreased
    count_resp = client.get("/public/notifications/unread-count", headers=_user_headers("user-1"))
    assert count_resp.json()["count"] == 0


def test_api_mark_read_not_found() -> None:
    client, _ = _make_app()
    resp = client.post("/public/notifications/nonexistent/read", headers=_user_headers("user-1"))
    assert resp.status_code == 404


def test_api_mark_all_read() -> None:
    client, repo = _make_app()
    repo.create(user_id="user-1", type="follow", actor_user_id="user-2", resource_id="user-2", resource_type="user")
    repo.create(user_id="user-1", type="comment_reply", actor_user_id="user-3", resource_id="post-1", resource_type="post")

    resp = client.post("/public/notifications/read-all", headers=_user_headers("user-1"))
    assert resp.status_code == 200
    assert resp.json()["status"] == "all_read"
    assert resp.json()["count"] == 2

    count_resp = client.get("/public/notifications/unread-count", headers=_user_headers("user-1"))
    assert count_resp.json()["count"] == 0


def test_api_notifications_user_scoped() -> None:
    client, repo = _make_app()
    repo.create(user_id="user-1", type="follow", actor_user_id="user-2", resource_id="user-2", resource_type="user")
    repo.create(user_id="user-2", type="follow", actor_user_id="user-3", resource_id="user-3", resource_type="user")

    resp = client.get("/public/notifications", headers=_user_headers("user-1"))
    assert len(resp.json()) == 1

    resp2 = client.get("/public/notifications", headers=_user_headers("user-2"))
    assert len(resp2.json()) == 1


def test_notification_includes_new_fields() -> None:
    repo = InMemoryNotificationRepository()
    notif = repo.create(
        user_id="user-2",
        type="comment_reply",
        actor_user_id="user-1",
        actor_display_name="User One",
        resource_id="post-1",
        resource_type="post",
        preview="Great point! I agree with...",
        group_key="comment_reply:post-1",
        link="/blog/test-post",
    )
    assert notif.preview == "Great point! I agree with..."
    assert notif.group_key == "comment_reply:post-1"
    assert notif.link == "/blog/test-post"

    summaries = repo.list_for_user("user-2")
    assert len(summaries) == 1
    assert summaries[0].preview == "Great point! I agree with..."
    assert summaries[0].group_key == "comment_reply:post-1"
    assert summaries[0].link == "/blog/test-post"


def test_comment_reply_notification_created_via_api() -> None:
    """Test that the API creates notifications with new fields visible."""
    client, repo = _make_app()
    notif = repo.create(
        user_id="user-1",
        type="comment_reply",
        actor_user_id="user-2",
        actor_display_name="User Two",
        resource_id="post-abc",
        resource_type="post",
        preview="This is a reply to your comment",
        group_key="comment_reply:post-abc",
        link="/blog/some-post",
    )
    assert notif.preview == "This is a reply to your comment"
    assert notif.link == "/blog/some-post"

    resp = client.get("/public/notifications", headers=_user_headers("user-1"))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["preview"] == "This is a reply to your comment"
    assert data[0]["group_key"] == "comment_reply:post-abc"
    assert data[0]["link"] == "/blog/some-post"
    assert data[0]["type"] == "comment_reply"
