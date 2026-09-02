"""Chat: answer a question over the org's documents, with citations.

The full read path in one place:

    user question
      -> persist the user message
      -> retrieve relevant chunks (RetrievalService)
      -> build a grounded prompt and call the LLM
      -> persist the assistant answer + citations (links to the source chunks)

Citations snapshot the source title and a snippet, so the answer stays
verifiable even if the document is later deleted. The service is tenant-bound via
its org-scoped conversation repository; retrieval is likewise org-scoped, so a
conversation can only ever draw on its own organization's knowledge.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.llm.base import LLMProvider
from app.models.citation import Citation
from app.models.conversation import Conversation
from app.models.enums import MessageRole
from app.models.message import Message
from app.models.user import User
from app.rag.engine import AnswerEngine, AnswerResult, LinearAnswerEngine
from app.repositories.conversation import ConversationRepository
from app.services.retrieval_service import DEFAULT_TOP_K, RetrievalService

logger = get_logger(__name__)

_TITLE_MAX = 60
_SNIPPET_MAX = 500


@dataclass(frozen=True)
class ChatResult:
    conversation: Conversation
    assistant_message: Message


class ChatService:
    def __init__(
        self,
        conversations: ConversationRepository,
        engine: AnswerEngine,
        *,
        retrieval: RetrievalService | None = None,
        llm: LLMProvider | None = None,
    ) -> None:
        self.conversations = conversations
        self.engine = engine
        self._retrieval = retrieval
        self._llm = llm

    @property
    def _session(self) -> AsyncSession:
        return self.conversations.session

    def resolve_engine(self, mode: Literal["linear", "agentic"] | None = None) -> AnswerEngine:
        if mode is None:
            return self.engine
        if mode == "agentic":
            from app.agents.engine import AgenticAnswerEngine

            if isinstance(self.engine, AgenticAnswerEngine):
                return self.engine
            if self._retrieval is not None and self._llm is not None:
                return AgenticAnswerEngine(
                    self._retrieval, self._llm, max_attempts=settings.AGENT_MAX_ATTEMPTS
                )
        elif mode == "linear":
            if isinstance(self.engine, LinearAnswerEngine):
                return self.engine
            if self._retrieval is not None and self._llm is not None:
                return LinearAnswerEngine(self._retrieval, self._llm)
        return self.engine

    async def send(
        self,
        *,
        conversation_id: uuid.UUID | None,
        user: User,
        message: str,
        top_k: int = DEFAULT_TOP_K,
        mode: Literal["linear", "agentic"] | None = None,
    ) -> ChatResult:
        conversation = await self._get_or_create_conversation(conversation_id, user, message)

        # 1. Record the user's turn.
        self._session.add(
            Message(
                org_id=self.conversations.org_id,
                conversation_id=conversation.id,
                role=MessageRole.USER,
                content=message,
            )
        )

        # 2. Produce a grounded answer (linear or agentic engine) + its sources.
        engine = self.resolve_engine(mode)
        result = await engine.answer(message, top_k=top_k)
        chunks = result.chunks

        # 3. Record the assistant's turn with citations to the sources used.
        assistant = Message(
            org_id=self.conversations.org_id,
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=result.answer,
        )
        assistant.citations = [
            Citation(
                chunk_id=uuid.UUID(chunk.chunk_id),
                document_id=uuid.UUID(chunk.document_id),
                rank=rank,
                document_title=chunk.document_title,
                snippet=chunk.content[:_SNIPPET_MAX],
            )
            for rank, chunk in enumerate(chunks, start=1)
        ]
        self._session.add(assistant)

        await self._session.commit()
        logger.info(
            "chat_answered",
            conversation_id=str(conversation.id),
            citations=len(assistant.citations),
        )
        return ChatResult(conversation=conversation, assistant_message=assistant)

    async def send_stream(
        self,
        *,
        conversation_id: uuid.UUID | None,
        user: User,
        message: str,
        top_k: int = DEFAULT_TOP_K,
        mode: Literal["linear", "agentic"] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        conversation = await self._get_or_create_conversation(conversation_id, user, message)

        # 1. Record user turn
        self._session.add(
            Message(
                org_id=self.conversations.org_id,
                conversation_id=conversation.id,
                role=MessageRole.USER,
                content=message,
            )
        )

        engine = self.resolve_engine(mode)
        result: AnswerResult | None = None

        async for item in engine.answer_stream(message, top_k=top_k):
            if item.get("event") == "result":
                result = item["data"]
            else:
                yield item

        if result is None:
            result = AnswerResult(answer="I was unable to generate an answer.", chunks=[])

        chunks = result.chunks

        # 2. Record assistant turn + citations
        assistant = Message(
            org_id=self.conversations.org_id,
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=result.answer,
        )
        assistant.citations = [
            Citation(
                chunk_id=uuid.UUID(chunk.chunk_id),
                document_id=uuid.UUID(chunk.document_id),
                rank=rank,
                document_title=chunk.document_title,
                snippet=chunk.content[:_SNIPPET_MAX],
            )
            for rank, chunk in enumerate(chunks, start=1)
        ]
        self._session.add(assistant)

        await self._session.commit()
        logger.info(
            "chat_answered_stream",
            conversation_id=str(conversation.id),
            citations=len(assistant.citations),
        )

        yield {
            "event": "done",
            "conversation_id": str(conversation.id),
            "message": {
                "id": str(assistant.id),
                "role": assistant.role.value,
                "content": assistant.content,
                "created_at": assistant.created_at.isoformat(),
                "citations": [
                    {
                        "rank": c.rank,
                        "document_id": str(c.document_id) if c.document_id else None,
                        "chunk_id": str(c.chunk_id) if c.chunk_id else None,
                        "document_title": c.document_title,
                        "snippet": c.snippet,
                    }
                    for c in assistant.citations
                ],
            },
        }

    async def _get_or_create_conversation(
        self, conversation_id: uuid.UUID | None, user: User, first_message: str
    ) -> Conversation:
        if conversation_id is not None:
            conversation = await self.conversations.get(conversation_id)
            if conversation is None:
                raise NotFoundError("Conversation not found.")
            return conversation

        conversation = Conversation(
            created_by_user_id=user.id,
            title=first_message.strip()[:_TITLE_MAX] or "New conversation",
        )
        self.conversations.add(conversation)  # stamps org_id
        await self._session.flush()
        return conversation
