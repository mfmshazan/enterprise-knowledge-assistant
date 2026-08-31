"""The LLM provider contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ChatMessage:
    """A single turn in a chat prompt. `role` is one of system|user|assistant."""

    role: str
    content: str


class LLMProvider(ABC):
    @property
    @abstractmethod
    def model(self) -> str:
        """Identifier of the underlying model."""

    @abstractmethod
    async def generate(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> str:
        """Return the assistant's completion for the given message list."""
