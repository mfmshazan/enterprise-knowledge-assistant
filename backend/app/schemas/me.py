"""The `/users/me` aggregate: the current user plus every org they belong to."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.membership import MembershipRead
from app.schemas.user import UserRead


class MeResponse(BaseModel):
    user: UserRead
    memberships: list[MembershipRead]
