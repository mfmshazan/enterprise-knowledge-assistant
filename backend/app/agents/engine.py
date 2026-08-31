"""AgenticAnswerEngine — runs the LangGraph agent and adapts it to AnswerEngine.

The final graph state carries the grounded answer plus the last set of retrieved
chunks, which become the message's citations. Same `AnswerResult` contract as the
linear engine, so ChatService is unaware of which strategy produced the answer.
"""

from __future__ import annotations

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
