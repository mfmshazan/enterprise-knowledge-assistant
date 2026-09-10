"""Schemas for system metadata endpoints.

These expose *non-secret* runtime configuration (model names, vector dimensions,
chat mode) so the frontend can display accurate system info instead of
hardcoding it. No API keys or connection strings are ever included here.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SystemConfigResponse(BaseModel):
    llm_provider: str = Field(examples=["gemini"])
    llm_model: str = Field(examples=["gemini-3.6-flash"])
    embedding_provider: str = Field(examples=["gemini"])
    embedding_model: str = Field(examples=["text-embedding-004"])
    embedding_dim: int = Field(examples=[768])
    vector_store: str = Field(examples=["Qdrant"])
    chat_mode: str = Field(examples=["agentic"])
