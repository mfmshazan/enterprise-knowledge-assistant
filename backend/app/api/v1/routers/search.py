"""Semantic search endpoint, mounted under /orgs/{org_id}/search.

Returns the chunks most relevant to a query within the org, with similarity
scores and their source document. This is retrieval on its own — the LLM answer
that consumes these results arrives in Phase 5.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import RetrievalServiceDep
from app.schemas.search import RetrievedChunkRead, SearchRequest, SearchResponse

router = APIRouter()


@router.post("", response_model=SearchResponse, summary="Semantic search over the org's documents")
async def search(payload: SearchRequest, service: RetrievalServiceDep) -> SearchResponse:
    results = await service.search(payload.query, top_k=payload.top_k)
    return SearchResponse(
        query=payload.query,
        results=[RetrievedChunkRead.model_validate(r, from_attributes=True) for r in results],
    )
