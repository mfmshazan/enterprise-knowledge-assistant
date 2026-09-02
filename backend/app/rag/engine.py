"""AnswerEngine: how a question becomes a grounded answer.

This is the seam between conversation management (ChatService) and the RAG
strategy. ChatService persists turns and citations; the engine decides *how* to
produce the answer + the source chunks that ground it. Two implementations:

* `LinearAnswerEngine` — a single pass: retrieve -> prompt -> generate.
* `AgenticAnswerEngine` (see app.agents) — a LangGraph multi-agent graph with a
  verification/self-correction loop.

Both return the same `AnswerResult`, so swapping strategies (via `CHAT_MODE`)
touches only the factory — the rest of the app is unchanged.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from app.llm.base import LLMProvider
from app.rag.prompts import build_grounded_messages
from app.services.retrieval_service import RetrievalService, RetrievedChunk


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    chunks: list[RetrievedChunk]


class AnswerEngine(ABC):
    @abstractmethod
    async def answer(self, question: str, *, top_k: int) -> AnswerResult:
        """Produce an answer to `question` plus the chunks that grounded it."""

    @abstractmethod
    async def answer_stream(self, question: str, *, top_k: int) -> AsyncIterator[dict[str, Any]]:
        """Yield real-time agent/retrieval steps and conclude with the AnswerResult."""
        if False:
            yield {}


class LinearAnswerEngine(AnswerEngine):
    def __init__(self, retrieval: RetrievalService, llm: LLMProvider) -> None:
        self.retrieval = retrieval
        self.llm = llm

    async def answer(self, question: str, *, top_k: int) -> AnswerResult:
        chunks = await self.retrieval.search(question, top_k=top_k)
        prompt = build_grounded_messages(question, chunks)
        answer = await self.llm.generate(prompt)
        return AnswerResult(answer=answer, chunks=chunks)

    async def answer_stream(self, question: str, *, top_k: int) -> AsyncIterator[dict[str, Any]]:
        yield {
            "event": "step",
            "step": "retrieve",
            "data": {"status": "Searching knowledge base for relevant context...", "top_k": top_k},
        }
        chunks = await self.retrieval.search(question, top_k=top_k)
        yield {
            "event": "step",
            "step": "retrieve",
            "data": {
                "status": f"Found {len(chunks)} relevant context passages",
                "chunks_count": len(chunks),
                "sources": [c.document_title for c in chunks],
            },
        }
        yield {
            "event": "step",
            "step": "generate",
            "data": {"status": "Generating grounded answer with citations..."},
        }
        prompt = build_grounded_messages(question, chunks)
        answer = await self.llm.generate(prompt)
        yield {"event": "result", "data": AnswerResult(answer=answer, chunks=chunks)}
