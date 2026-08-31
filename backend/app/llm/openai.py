"""OpenAI-compatible chat LLM provider (serves OpenAI and Gemini).

Low temperature by default: for grounded RAG answers we want faithful,
low-variance responses, not creative ones.
"""

from __future__ import annotations

from typing import Any, cast

from openai import AsyncOpenAI

from app.llm.base import ChatMessage, LLMProvider


class OpenAICompatibleLLMProvider(LLMProvider):
    def __init__(self, *, api_key: str, model: str, base_url: str | None = None) -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
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
        # The OpenAI SDK's message param is a union of TypedDicts; our simple
        # {role, content} dicts are valid at runtime, so cast to satisfy typing.
        payload = cast("Any", [{"role": m.role, "content": m.content} for m in messages])
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=payload,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
