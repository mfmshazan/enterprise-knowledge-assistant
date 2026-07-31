"""Membership response schemas.

Two views of the same join, depending on direction:
* `MembershipRead` — "my membership": the org plus my role (used in /users/me
  and 'list my orgs').
* `OrgMemberRead` — "a member of this org": the user plus their role (used in
  'list org members').
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Role
from app.schemas.organization import OrganizationRead
from app.schemas.user import UserRead


class MembershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: Role
    created_at: datetime
    organization: OrganizationRead


class OrgMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: Role
    created_at: datetime
    user: UserRead


class MemberRoleUpdate(BaseModel):
    role: Role = Field(description="New role to assign to the member.")
