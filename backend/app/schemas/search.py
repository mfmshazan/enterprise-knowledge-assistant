"""Search request/response schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.services.retrieval_service import DEFAULT_TOP_K, MAX_TOP_K


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000, examples=["What is our refund policy?"])
    top_k: int = Field(default=DEFAULT_TOP_K, ge=1, le=MAX_TOP_K)


class RetrievedChunkRead(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_title: str
    chunk_index: int
    content: str
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[RetrievedChunkRead]
