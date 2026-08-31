"""Deterministic fake LLM for tests — no API key, no network.

Produces a stable, citation-shaped answer so the chat pipeline (prompting,
persistence, citation attachment) can be tested end to end without a real model.
"""

from __future__ import annotations

from app.llm.base import ChatMessage, LLMProvider


class FakeLLMProvider(LLMProvider):
    def __init__(self, *, model: str = "fake-llm") -> None:
        self._model = model

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
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        # Echo a short slice of the question so tests can assert the prompt flowed
        # through, and always emit a [1] citation marker.
        head = last_user.strip().splitlines()[0][:80] if last_user.strip() else "your question"
        return f"Based on the provided context, here is a grounded answer to: {head} [1]"
