"""Response schemas for the health/readiness endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    version: str = Field(examples=["0.1.0"])
    environment: str = Field(examples=["development"])


class ReadinessResponse(BaseModel):
    status: str = Field(examples=["ok"])
    checks: dict[str, str] = Field(
        description="Per-dependency status.",
        examples=[{"database": "ok", "redis": "ok"}],
    )
