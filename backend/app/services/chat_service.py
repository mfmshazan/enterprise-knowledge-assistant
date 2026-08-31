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
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.citation import Citation
from app.models.conversation import Conversation
from app.models.enums import MessageRole
from app.models.message import Message
from app.models.user import User
from app.rag.engine import AnswerEngine
from app.repositories.conversation import ConversationRepository
from app.services.retrieval_service import DEFAULT_TOP_K

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
    ) -> None:
        self.conversations = conversations
        self.engine = engine

    @property
    def _session(self) -> AsyncSession:
        return self.conversations.session

    async def send(
        self,
        *,
        conversation_id: uuid.UUID | None,
        user: User,
        message: str,
        top_k: int = DEFAULT_TOP_K,
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
        result = await self.engine.answer(message, top_k=top_k)
        chunks = result.chunks

        # 3. Record the assistant's turn with citations to the sources used.
        assistant = Message(
            org_id=self.conversations.org_id,
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=result.answer,
        )
        # Assign the collection (not append) so it is a *loaded* relationship even
        # when empty — otherwise serializing `.citations` after commit would
        # trigger an illegal async lazy-load.
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
