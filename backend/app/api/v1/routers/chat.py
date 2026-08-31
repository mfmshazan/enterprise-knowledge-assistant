"""Chat endpoints, mounted under /orgs/{org_id}/chat.

Ask a question and get a grounded, cited answer over the org's documents; list
past conversations; and load a conversation's full history. Members only.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.api.deps import ChatServiceDep, CurrentMembership, CurrentUser, DbSession
from app.core.exceptions import NotFoundError
from app.repositories.conversation import ConversationRepository
from app.schemas.chat import (
    ChatMessageRead,
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ConversationSummary,
)

router = APIRouter()


@router.post("", response_model=ChatResponse, summary="Ask a question (grounded, cited answer)")
async def send_message(
    payload: ChatRequest,
    service: ChatServiceDep,
    user: CurrentUser,
) -> ChatResponse:
    result = await service.send(
        conversation_id=payload.conversation_id,
        user=user,
        message=payload.message,
        top_k=payload.top_k,
    )
    return ChatResponse(
        conversation_id=result.conversation.id,
        message=ChatMessageRead.model_validate(result.assistant_message),
    )


@router.get(
    "/conversations",
    response_model=list[ConversationSummary],
    summary="List conversations in the org",
)
async def list_conversations(
    db: DbSession, membership: CurrentMembership
) -> list[ConversationSummary]:
    conversations = await ConversationRepository(db, membership.org_id).list_recent()
    return [ConversationSummary.model_validate(c) for c in conversations]


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetail,
    summary="Get a conversation with its full message history",
)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: DbSession,
    membership: CurrentMembership,
) -> ConversationDetail:
    conversation = await ConversationRepository(db, membership.org_id).get_with_messages(
        conversation_id
    )
    if conversation is None:
        raise NotFoundError("Conversation not found.")
    return ConversationDetail.model_validate(conversation)
