"""Domain enums shared by models, schemas, and RBAC dependencies."""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    """A member's role *within a single organization*.

    `StrEnum` makes the value JSON-serializable and stored as plain text. Roles
    are hierarchical: OWNER outranks ADMIN outranks MEMBER. `rank` powers the
    `require_role` RBAC check (a higher rank satisfies a lower requirement).
    """

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"

    @property
    def rank(self) -> int:
        return _ROLE_RANK[self]

    def satisfies(self, required: Role) -> bool:
        """True if this role meets or exceeds the required role."""
        return self.rank >= required.rank


_ROLE_RANK: dict[Role, int] = {
    Role.MEMBER: 1,
    Role.ADMIN: 2,
    Role.OWNER: 3,
}
