"""API Key schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    expires_in_days: int | None = Field(default=None, ge=1, le=365)


class ApiKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    key_prefix: str
    created_by_user_id: uuid.UUID | None
    expires_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime
    is_active: bool


class ApiKeyCreatedResponse(ApiKeyRead):
    secret_key: str = Field(
        description="Plaintext API secret key. Displayed only once upon creation."
    )
