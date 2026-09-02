"""AgenticAnswerEngine — runs the LangGraph agent and adapts it to AnswerEngine.

The final graph state carries the grounded answer plus the last set of retrieved
chunks, which become the message's citations. Same `AnswerResult` contract as the
linear engine, so ChatService is unaware of which strategy produced the answer.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from app.agents.graph import build_agent_graph
from app.agents.state import AgentState
from app.llm.base import LLMProvider
from app.rag.engine import AnswerEngine, AnswerResult
from app.services.retrieval_service import RetrievalService, RetrievedChunk


class AgenticAnswerEngine(AnswerEngine):
    def __init__(
        self,
        retrieval: RetrievalService,
        llm: LLMProvider,
        *,
        max_attempts: int = 2,
    ) -> None:
        self._graph = build_agent_graph(retrieval, llm, max_attempts=max_attempts)
        self._max_attempts = max_attempts

    async def answer(self, question: str, *, top_k: int) -> AnswerResult:
        initial: AgentState = {
            "question": question,
            "top_k": top_k,
            "max_attempts": self._max_attempts,
            "attempts": 0,
        }
        final = await self._graph.ainvoke(initial)
        chunks: list[RetrievedChunk] = final.get("chunks", [])
        return AnswerResult(answer=final.get("answer", ""), chunks=chunks)

    async def answer_stream(self, question: str, *, top_k: int) -> AsyncIterator[dict[str, Any]]:
        initial: AgentState = {
            "question": question,
            "top_k": top_k,
            "max_attempts": self._max_attempts,
            "attempts": 0,
        }
        latest_chunks: list[RetrievedChunk] = []
        final_answer: str = ""

        yield {
            "event": "step",
            "step": "start",
            "data": {
                "status": "Initializing agent graph (Plan -> Retrieve -> Generate -> Verify)..."
            },
        }

        async for event in self._graph.astream(initial, stream_mode="updates"):
            if "plan" in event:
                plan_data = event["plan"]
                search_query = plan_data.get("search_query", question)
                yield {
                    "event": "step",
                    "step": "plan",
                    "data": {
                        "status": f"Rewriting query for retrieval: '{search_query}'",
                        "search_query": search_query,
                    },
                }
            if "retrieve" in event:
                ret_data = event["retrieve"]
                latest_chunks = ret_data.get("chunks", [])
                yield {
                    "event": "step",
                    "step": "retrieve",
                    "data": {
                        "status": f"Retrieved {len(latest_chunks)} passages from knowledge base",
                        "chunks_count": len(latest_chunks),
                        "sources": [c.document_title for c in latest_chunks],
                    },
                }
            if "generate" in event:
                yield {
                    "event": "step",
                    "step": "generate",
                    "data": {
                        "status": "Drafting candidate response from context passages...",
                    },
                }
            if "verify" in event:
                ver_data = event["verify"]
                grounded = ver_data.get("grounded", False)
                attempts = ver_data.get("attempts", 1)
                if grounded:
                    status_text = (
                        "Factual grounding check PASSED ✅ (Draft fully supported by context)"
                    )
                else:
                    status_text = (
                        f"Grounding check FAILED ⚠️ (Attempt {attempts}/{self._max_attempts}: "
                        "Expanding context and retrying)"
                    )
                yield {
                    "event": "step",
                    "step": "verify",
                    "data": {
                        "grounded": grounded,
                        "attempt": attempts,
                        "max_attempts": self._max_attempts,
                        "status": status_text,
                    },
                }
            if "finalize" in event:
                final_answer = event["finalize"].get("answer", "")
                yield {
                    "event": "step",
                    "step": "finalize",
                    "data": {"status": "Finalizing grounded answer with citations."},
                }

        yield {
            "event": "result",
            "data": AnswerResult(answer=final_answer, chunks=latest_chunks),
        }
