"""Contact message public submission and admin review."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, Field
from pydantic.networks import EmailStr
from sqlalchemy import Engine, insert, select, update

from backend.app.database import contact_messages


class ContactMessage(BaseModel):
    id: str
    name: str
    email: str
    subject: str
    message: str
    read_at: datetime | None = None
    created_at: datetime


class ContactMessageCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    subject: str = Field(min_length=1, max_length=500)
    message: str = Field(min_length=1, max_length=10000)


class ContactMessageAdmin(BaseModel):
    id: str
    name: str
    email: str
    subject: str
    message: str
    read_at: datetime | None = None
    created_at: datetime


class ContactMessageRepository(Protocol):
    def create(self, request: ContactMessageCreate) -> ContactMessage: ...
    def list_all(self) -> list[ContactMessageAdmin]: ...
    def get_by_id(self, message_id: str) -> ContactMessageAdmin | None: ...
    def mark_read(self, message_id: str) -> ContactMessageAdmin | None: ...


class InMemoryContactMessageRepository:
    def __init__(self) -> None:
        self._messages: dict[str, ContactMessage] = {}

    def create(self, request: ContactMessageCreate) -> ContactMessage:
        msg = ContactMessage(
            id=uuid4().hex,
            name=request.name,
            email=request.email,
            subject=request.subject,
            message=request.message,
            created_at=datetime.now(UTC),
        )
        self._messages[msg.id] = msg
        return msg

    def list_all(self) -> list[ContactMessageAdmin]:
        return [
            ContactMessageAdmin(
                id=m.id,
                name=m.name,
                email=m.email,
                subject=m.subject,
                message=m.message,
                read_at=m.read_at,
                created_at=m.created_at,
            )
            for m in sorted(self._messages.values(), key=lambda m: m.created_at, reverse=True)
        ]

    def get_by_id(self, message_id: str) -> ContactMessageAdmin | None:
        m = self._messages.get(message_id)
        if m is None:
            return None
        return ContactMessageAdmin(
            id=m.id,
            name=m.name,
            email=m.email,
            subject=m.subject,
            message=m.message,
            read_at=m.read_at,
            created_at=m.created_at,
        )

    def mark_read(self, message_id: str) -> ContactMessageAdmin | None:
        m = self._messages.get(message_id)
        if m is None:
            return None
        m.read_at = datetime.now(UTC)
        return ContactMessageAdmin(
            id=m.id,
            name=m.name,
            email=m.email,
            subject=m.subject,
            message=m.message,
            read_at=m.read_at,
            created_at=m.created_at,
        )


class PostgresContactMessageRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create(self, request: ContactMessageCreate) -> ContactMessage:
        now = datetime.now(UTC)
        msg_id = uuid4().hex
        with self._engine.begin() as conn:
            conn.execute(
                insert(contact_messages).values(
                    id=msg_id,
                    name=request.name,
                    email=request.email,
                    subject=request.subject,
                    message=request.message,
                    created_at=now,
                )
            )
        return ContactMessage(
            id=msg_id,
            name=request.name,
            email=request.email,
            subject=request.subject,
            message=request.message,
            created_at=now,
        )

    def list_all(self) -> list[ContactMessageAdmin]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                select(contact_messages).order_by(contact_messages.c.created_at.desc())
            ).mappings()
            return [
                ContactMessageAdmin(
                    id=row["id"],
                    name=row["name"],
                    email=row["email"],
                    subject=row["subject"],
                    message=row["message"],
                    read_at=row["read_at"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

    def get_by_id(self, message_id: str) -> ContactMessageAdmin | None:
        with self._engine.connect() as conn:
            row = (
                conn.execute(
                    select(contact_messages).where(contact_messages.c.id == message_id)
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                return None
            return ContactMessageAdmin(
                id=row["id"],
                name=row["name"],
                email=row["email"],
                subject=row["subject"],
                message=row["message"],
                read_at=row["read_at"],
                created_at=row["created_at"],
            )

    def mark_read(self, message_id: str) -> ContactMessageAdmin | None:
        now = datetime.now(UTC)
        with self._engine.begin() as conn:
            result = conn.execute(
                update(contact_messages)
                .where(contact_messages.c.id == message_id)
                .values(read_at=now)
            )
            if result.rowcount == 0:
                return None
        return self.get_by_id(message_id)
