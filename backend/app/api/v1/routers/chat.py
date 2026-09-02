"""Chat endpoints, mounted under /orgs/{org_id}/chat.

Ask a question and get a grounded, cited answer over the org's documents; list
past conversations; and load a conversation's full history. Members only.
"""

from __future__ import annotations

import json
import uuid

from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

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
        mode=payload.mode,
    )
    return ChatResponse(
        conversation_id=result.conversation.id,
        message=ChatMessageRead.model_validate(result.assistant_message),
    )


@router.post(
    "/stream", summary="Ask a question with real-time SSE stream of agent steps and citations"
)
async def stream_message(
    payload: ChatRequest,
    service: ChatServiceDep,
    user: CurrentUser,
) -> StreamingResponse:
    async def event_generator() -> AsyncIterator[str]:
        try:
            async for item in service.send_stream(
                conversation_id=payload.conversation_id,
                user=user,
                message=payload.message,
                top_k=payload.top_k,
                mode=payload.mode,
            ):
                yield f"data: {json.dumps(item)}\n\n"
        except Exception as e:
            error_payload = {"event": "error", "error": str(e)}
            yield f"data: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
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
