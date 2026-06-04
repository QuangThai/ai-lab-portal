"""Tests for contact message public submission and admin review."""

from __future__ import annotations

import json
from time import time

from fastapi.testclient import TestClient

from backend.app.admin_boundary import ADMIN_IDENTITY_HEADER, ADMIN_SIGNATURE_HEADER, sign_admin_identity
from backend.app.contact import (
    ContactMessageAdmin,
    ContactMessageCreate,
    ContactMessageRepository,
    InMemoryContactMessageRepository,
)
from backend.app.main import create_app
from backend.app.settings import Settings


TEST_SECRET = Settings(environment="test").admin_boundary_secret.get_secret_value()


def _admin_headers() -> dict[str, str]:
    now = int(time())
    identity = {"user_id":"admin-1","email":"admin@test.com","role":"admin","issued_at":now}
    payload = json.dumps(identity)
    return {
        ADMIN_IDENTITY_HEADER: payload,
        ADMIN_SIGNATURE_HEADER: sign_admin_identity(payload, TEST_SECRET),
    }


def _test_repo() -> ContactMessageRepository:
    return InMemoryContactMessageRepository()


def _make_body(
    name: str = "John Doe",
    email: str = "john@example.com",
    subject: str = "Test Subject",
    message: str = "This is a test message body.",
) -> dict[str, str]:
    return {"name": name, "email": email, "subject": subject, "message": message}


def test_public_submit_contact_message() -> None:
    repo = _test_repo()
    app = create_app(contact_repository=repo)
    client = TestClient(app)
    body = _make_body()
    resp = client.post("/public/contact", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "received"
    assert "id" in data


def test_public_submit_requires_name() -> None:
    repo = _test_repo()
    app = create_app(contact_repository=repo)
    client = TestClient(app)
    body = _make_body(name="")
    resp = client.post("/public/contact", json=body)
    assert resp.status_code == 422


def test_public_submit_requires_valid_email() -> None:
    repo = _test_repo()
    app = create_app(contact_repository=repo)
    client = TestClient(app)
    body = _make_body(email="not-an-email")
    resp = client.post("/public/contact", json=body)
    assert resp.status_code == 422


def test_public_submit_requires_subject() -> None:
    repo = _test_repo()
    app = create_app(contact_repository=repo)
    client = TestClient(app)
    body = _make_body(subject="")
    resp = client.post("/public/contact", json=body)
    assert resp.status_code == 422


def test_public_submit_requires_message() -> None:
    repo = _test_repo()
    app = create_app(contact_repository=repo)
    client = TestClient(app)
    body = _make_body(message="")
    resp = client.post("/public/contact", json=body)
    assert resp.status_code == 422


def test_admin_list_contact_messages() -> None:
    repo = _test_repo()
    repo.create(ContactMessageCreate(**_make_body(name="Alice")))
    app = create_app(contact_repository=repo)
    client = TestClient(app)
    resp = client.get("/admin/contact-messages", headers=_admin_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Alice"
    assert data[0]["subject"] == "Test Subject"


def test_admin_get_contact_message() -> None:
    repo = _test_repo()
    msg = repo.create(ContactMessageCreate(**_make_body(name="Bob")))
    app = create_app(contact_repository=repo)
    client = TestClient(app)
    resp = client.get(
        f"/admin/contact-messages/{msg.id}",
        headers=_admin_headers(),
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Bob"


def test_admin_get_contact_message_not_found() -> None:
    repo = _test_repo()
    app = create_app(contact_repository=repo)
    client = TestClient(app)
    resp = client.get(
        "/admin/contact-messages/nonexistent",
        headers=_admin_headers(),
    )
    assert resp.status_code == 404


def test_admin_mark_read() -> None:
    repo = _test_repo()
    msg = repo.create(ContactMessageCreate(**_make_body()))
    assert msg.read_at is None
    app = create_app(contact_repository=repo)
    client = TestClient(app)
    resp = client.patch(
        f"/admin/contact-messages/{msg.id}/read",
        headers=_admin_headers(),
    )
    assert resp.status_code == 200
    assert resp.json()["read_at"] is not None


def test_admin_mark_read_not_found() -> None:
    repo = _test_repo()
    app = create_app(contact_repository=repo)
    client = TestClient(app)
    resp = client.patch(
        "/admin/contact-messages/nonexistent/read",
        headers=_admin_headers(),
    )
    assert resp.status_code == 404


def test_admin_list_requires_auth() -> None:
    repo = _test_repo()
    app = create_app(contact_repository=repo)
    client = TestClient(app)
    resp = client.get("/admin/contact-messages")
    assert resp.status_code == 401


def test_stored_message_fields_match() -> None:
    repo = _test_repo()
    msg = repo.create(ContactMessageCreate(**_make_body(
        name="Test User",
        email="test@example.com",
        subject="Inquiry",
        message="Hello, I have a question.",
    )))
    assert msg.name == "Test User"
    assert msg.email == "test@example.com"
    assert msg.subject == "Inquiry"
    assert msg.message == "Hello, I have a question."
    assert msg.read_at is None
    assert msg.created_at is not None
