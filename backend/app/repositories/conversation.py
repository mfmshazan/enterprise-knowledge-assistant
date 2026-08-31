"""Conversation data access — org-scoped."""

from __future__ import annotations

import uuid

from sqlalchemy import desc
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.base import OrgScopedRepository


class ConversationRepository(OrgScopedRepository[Conversation]):
    model = Conversation

    async def list_recent(self, *, limit: int = 50) -> list[Conversation]:
        result = await self.session.scalars(
            self._scoped().order_by(desc(Conversation.created_at)).limit(limit)
        )
        return list(result.all())

    async def get_with_messages(self, conversation_id: uuid.UUID) -> Conversation | None:
        """Load a conversation with its messages and each message's citations
        eagerly, so the full history serializes without lazy loads."""
        return await self.session.scalar(
            self._scoped()
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.messages).selectinload(Message.citations))
        )
