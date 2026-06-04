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
USER_IDENTITY_HEADER = "x-ai-lab-user-identity"
USER_SIGNATURE_HEADER = "x-ai-lab-user-signature"
MAX_IDENTITY_AGE_SECONDS = 300


class SignedIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1, max_length=128)
    email: str = Field(min_length=3, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    role: Literal["admin", "user"]
    issued_at: int = Field(ge=0)


# Backward-compatible alias
AdminIdentity = SignedIdentity


def sign_admin_identity(identity_payload: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), identity_payload.encode("utf-8"), sha256).hexdigest()


def parse_identity(
    identity_payload: str,
    signature: str,
    settings: Settings | None = None,
) -> SignedIdentity:
    resolved_settings = settings or get_settings()
    expected_signature = sign_admin_identity(identity_payload, resolved_settings.admin_boundary_secret.get_secret_value())

    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid identity signature")

    try:
        payload = json.loads(identity_payload)
        identity = SignedIdentity.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid identity") from exc

    if int(time()) - identity.issued_at > MAX_IDENTITY_AGE_SECONDS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired identity")

    return identity


# Backward-compatible alias
parse_admin_identity = parse_identity


def require_admin_identity(
    identity_payload: Annotated[str | None, Header(alias=ADMIN_IDENTITY_HEADER)] = None,
    signature: Annotated[str | None, Header(alias=ADMIN_SIGNATURE_HEADER)] = None,
) -> SignedIdentity:
    return require_admin_identity_with_settings(get_settings(), identity_payload, signature)


def require_admin_identity_with_settings(
    settings: Settings,
    identity_payload: str | None,
    signature: str | None,
) -> SignedIdentity:
    if not identity_payload or not signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing admin identity")

    identity = parse_identity(identity_payload, signature, settings)
    if identity.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return identity


def require_user_identity(
    identity_payload: Annotated[str | None, Header(alias=USER_IDENTITY_HEADER)] = None,
    signature: Annotated[str | None, Header(alias=USER_SIGNATURE_HEADER)] = None,
) -> SignedIdentity:
    return require_user_identity_with_settings(get_settings(), identity_payload, signature)


def require_user_identity_with_settings(
    settings: Settings,
    identity_payload: str | None,
    signature: str | None,
) -> SignedIdentity:
    if not identity_payload or not signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user identity")

    identity = parse_identity(identity_payload, signature, settings)
    if identity.role not in ("user", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User or admin role required")
    return identity
