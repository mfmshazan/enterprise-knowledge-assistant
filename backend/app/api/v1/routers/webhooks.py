"""Inbound webhooks.

The Clerk webhook is how our database learns about identity lifecycle events that
happen *outside* a normal API request — a user being deleted, an email changed,
an org renamed. JIT provisioning (see IdentityService) covers create/read on the
fast path; webhooks cover the events JIT cannot observe.

STATUS: stub. This endpoint currently acknowledges receipt only. Before enabling
it in production it MUST verify the Svix signature using `CLERK_WEBHOOK_SECRET`
(Clerk sends `svix-id`, `svix-timestamp`, `svix-signature` headers) and then
dispatch on `event.type` to sync/soft-delete local rows. Tracked for a later
step; kept here so the route and contract exist.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/clerk", summary="Clerk lifecycle webhook (stub — verification pending)")
async def clerk_webhook(request: Request) -> dict[str, Any]:
    payload = await request.json()
    event_type = payload.get("type", "unknown")
    logger.info("clerk_webhook_received", event_type=event_type)
    # TODO: verify Svix signature, then handle user.created/updated/deleted and
    # organization.* / organizationMembership.* events.
    return {"status": "received", "event_type": event_type}
