"""Current-user endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.repositories.membership import MembershipRepository
from app.schemas.me import MeResponse

router = APIRouter()


@router.get("/me", response_model=MeResponse, summary="Get the current user and memberships")
async def read_me(user: CurrentUser, db: DbSession) -> MeResponse:
    """Return the authenticated user together with every organization they belong
    to (and their role in each). Hitting this endpoint also *provisions* the user
    on first login via the `get_current_user` dependency."""
    memberships = await MembershipRepository(db).list_for_user(user.id)
    return MeResponse.model_validate({"user": user, "memberships": memberships})
