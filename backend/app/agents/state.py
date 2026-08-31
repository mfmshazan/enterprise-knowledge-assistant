"""Shared state passed between agent nodes.

LangGraph threads a single mutable state dict through the graph; each node returns
a partial update that is merged in. `total=False` lets nodes populate keys
incrementally as the graph progresses.
"""

from __future__ import annotations

from typing import TypedDict

from app.services.retrieval_service import RetrievedChunk


class AgentState(TypedDict, total=False):
    # Inputs
    question: str
    top_k: int
    max_attempts: int

    # Working state
    search_query: str
    chunks: list[RetrievedChunk]
    draft: str
    grounded: bool
    attempts: int

    # Output
    answer: str
