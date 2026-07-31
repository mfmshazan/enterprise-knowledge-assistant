"""Aggregates all v1 resource routers into a single APIRouter.

As new resources land (auth, orgs, documents, chat, search, admin) they get one
line here. `main.py` only ever mounts this one router, keeping the app factory
stable across phases.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routers import organizations, users, webhooks

api_router = APIRouter()

# Health/readiness are mounted at the app root in main.py (infra probes expect
# them there), so they are intentionally NOT included here.

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(organizations.router, prefix="/orgs", tags=["organizations"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])

# Future phases:
# api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
# api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
