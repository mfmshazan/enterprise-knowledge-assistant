"""Deterministic fake LLM for tests — no API key, no network.

Produces a stable, citation-shaped answer so the chat pipeline (prompting,
persistence, citation attachment) can be tested end to end without a real model.
"""

from __future__ import annotations

from app.llm.base import ChatMessage, LLMProvider


class FakeLLMProvider(LLMProvider):
    """Deterministic fake that responds appropriately to each agent role.

    It inspects the system prompt to tell planner/verifier/generator apart so the
    LangGraph agent runs to completion in tests. `always_grounded=False` forces
    the verifier to reject drafts, exercising the self-correction/retry path.
    """

    def __init__(self, *, model: str = "fake-llm", always_grounded: bool = True) -> None:
        self._model = model
        self._always_grounded = always_grounded

    @property
    def model(self) -> str:
        return self._model

    async def generate(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> str:
        system = " ".join(m.content for m in messages if m.role == "system").lower()
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")

        if "query planner" in system:
            # Return the question unchanged as the search query.
            return last_user.strip().splitlines()[0] if last_user.strip() else "query"
        if "grounding verifier" in system:
            return "GROUNDED" if self._always_grounded else "NOT_GROUNDED"

        head = last_user.strip().splitlines()[0][:80] if last_user.strip() else "your question"
        return f"Based on the provided context, here is a grounded answer to: {head} [1]"
