import hmac
import json
from hashlib import sha256
from time import time
from typing import Annotated, Literal

from fastapi import Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from backend.app.settings import Settings, get_settings

ADMIN_IDENTITY_HEADER = "x-ai-lab-admin-identity"
ADMIN_SIGNATURE_HEADER = "x-ai-lab-admin-signature"
MAX_IDENTITY_AGE_SECONDS = 300


class AdminIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1, max_length=128)
    email: str = Field(min_length=3, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    role: Literal["admin"]
    issued_at: int = Field(ge=0)


def sign_admin_identity(identity_payload: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), identity_payload.encode("utf-8"), sha256).hexdigest()


def parse_admin_identity(identity_payload: str, signature: str, settings: Settings | None = None) -> AdminIdentity:
    resolved_settings = settings or get_settings()
    expected_signature = sign_admin_identity(identity_payload, resolved_settings.admin_boundary_secret.get_secret_value())

    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin identity signature")

    try:
        payload = json.loads(identity_payload)
        identity = AdminIdentity.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin identity") from exc

    if int(time()) - identity.issued_at > MAX_IDENTITY_AGE_SECONDS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired admin identity")

    return identity


def require_admin_identity(
    identity_payload: Annotated[str | None, Header(alias=ADMIN_IDENTITY_HEADER)] = None,
    signature: Annotated[str | None, Header(alias=ADMIN_SIGNATURE_HEADER)] = None,
) -> AdminIdentity:
    return require_admin_identity_with_settings(get_settings(), identity_payload, signature)


def require_admin_identity_with_settings(
    settings: Settings,
    identity_payload: str | None,
    signature: str | None,
) -> AdminIdentity:
    if not identity_payload or not signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing admin identity")

    return parse_admin_identity(identity_payload, signature, settings)
