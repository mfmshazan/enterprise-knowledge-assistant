"""System metadata endpoints.

Exposes non-secret runtime configuration (which models and vector settings are
active) so the frontend dashboard shows accurate, live system info rather than
hardcoded values. Read-only and free of secrets, so no auth is required.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.meta import SystemConfigResponse

router = APIRouter()


@router.get("/config", response_model=SystemConfigResponse, summary="Active system configuration")
async def get_config() -> SystemConfigResponse:
    return SystemConfigResponse(
        llm_provider=settings.LLM_PROVIDER,
        llm_model=settings.LLM_MODEL,
        embedding_provider=settings.EMBEDDING_PROVIDER,
        embedding_model=settings.EMBEDDING_MODEL,
        embedding_dim=settings.EMBEDDING_DIM,
        vector_store="Qdrant",
        chat_mode=settings.CHAT_MODE,
    )
