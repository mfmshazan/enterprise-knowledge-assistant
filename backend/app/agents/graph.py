"""The agentic RAG graph.

Flow:

    plan ─▶ retrieve ─▶ generate ─▶ verify ─┬─(grounded / out of tries)─▶ finalize ─▶ END
      ▲                                       │
      └───────────(not grounded)──────────────┘

* **plan** rewrites the question into a focused search query.
* **retrieve** runs org-scoped vector search for that query.
* **generate** drafts a grounded, cited answer from the retrieved passages.
* **verify** asks the model whether the draft is fully supported by the context.
  If not — and we still have attempts left — the graph loops back, widening the
  retrieval each time (self-correction). This is the core hallucination-reduction
  mechanism: an ungrounded draft is caught and re-attempted rather than returned.

Nodes call our own `RetrievalService`/`LLMProvider` (not LangChain wrappers), so
the provider abstraction and Gemini/OpenAI swap still hold. Dependencies are
closed over at build time, keeping node signatures LangGraph-native.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.prompts import PLANNER_SYSTEM, VERIFIER_SYSTEM
from app.agents.state import AgentState
from app.core.logging import get_logger
from app.llm.base import ChatMessage, LLMProvider
from app.rag.prompts import build_grounded_messages
from app.services.retrieval_service import MAX_TOP_K, RetrievalService

logger = get_logger(__name__)

_RETRY_TOP_K_STEP = 3


def build_agent_graph(
    retrieval: RetrievalService,
    llm: LLMProvider,
    *,
    max_attempts: int = 2,
) -> CompiledStateGraph:
    async def plan(state: AgentState) -> dict[str, Any]:
        question = state["question"]
        messages = [
            ChatMessage(role="system", content=PLANNER_SYSTEM),
            ChatMessage(role="user", content=question),
        ]
        query = (await llm.generate(messages, temperature=0.0)).strip()
        return {"search_query": query or question}

    async def retrieve(state: AgentState) -> dict[str, Any]:
        chunks = await retrieval.search(state["search_query"], top_k=state["top_k"])
        return {"chunks": chunks}

    async def generate(state: AgentState) -> dict[str, Any]:
        messages = build_grounded_messages(state["question"], state["chunks"])
        draft = await llm.generate(messages)
        return {"draft": draft}

    async def verify(state: AgentState) -> dict[str, Any]:
        attempts = state.get("attempts", 0) + 1
        chunks = state["chunks"]
        # Nothing to verify against -> accept the draft (it will say "I don't know").
        if not chunks:
            return {"grounded": True, "attempts": attempts, "answer": state["draft"]}

        context = "\n\n".join(f"[{i}] {c.content}" for i, c in enumerate(chunks, start=1))
        messages = [
            ChatMessage(role="system", content=VERIFIER_SYSTEM),
            ChatMessage(
                role="user",
                content=f"Context passages:\n{context}\n\nDraft answer:\n{state['draft']}",
            ),
        ]
        verdict = (await llm.generate(messages, temperature=0.0)).strip().upper()
        grounded = "NOT_GROUNDED" not in verdict

        update: dict[str, Any] = {"grounded": grounded, "attempts": attempts}
        if grounded:
            update["answer"] = state["draft"]
        else:
            # Widen retrieval on the next attempt to gather more evidence.
            update["top_k"] = min(state["top_k"] + _RETRY_TOP_K_STEP, MAX_TOP_K)
            logger.info("agent_answer_not_grounded_retrying", attempt=attempts)
        return update

    def route_after_verify(state: AgentState) -> str:
        if state.get("grounded") or state.get("attempts", 0) >= state["max_attempts"]:
            return "finalize"
        return "plan"

    async def finalize(state: AgentState) -> dict[str, Any]:
        # If we ran out of attempts without grounding, still return the best draft.
        return {"answer": state.get("answer") or state.get("draft", "")}

    graph: StateGraph = StateGraph(AgentState)
    graph.add_node("plan", plan)
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate)
    graph.add_node("verify", verify)
    graph.add_node("finalize", finalize)

    graph.set_entry_point("plan")
    graph.add_edge("plan", "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", "verify")
    graph.add_conditional_edges(
        "verify", route_after_verify, {"plan": "plan", "finalize": "finalize"}
    )
    graph.add_edge("finalize", END)

    return graph.compile()
