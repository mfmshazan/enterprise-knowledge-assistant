"""Organization request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255, examples=["Acme Inc."])
    slug: str | None = Field(
        default=None,
        max_length=255,
        description="Optional URL handle; derived from name if omitted.",
        examples=["acme"],
    )


class OrganizationRead(BaseModel):
    # from_attributes lets us build this straight from a SQLAlchemy model.
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime
