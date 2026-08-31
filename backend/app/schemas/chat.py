"""Chat request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MessageRole
from app.services.retrieval_service import DEFAULT_TOP_K, MAX_TOP_K


class ChatRequest(BaseModel):
    conversation_id: uuid.UUID | None = Field(
        default=None, description="Continue an existing conversation, or omit to start a new one."
    )
    message: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=DEFAULT_TOP_K, ge=1, le=MAX_TOP_K)


class CitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rank: int
    document_id: uuid.UUID | None
    chunk_id: uuid.UUID | None
    document_title: str
    snippet: str


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: MessageRole
    content: str
    created_at: datetime
    citations: list[CitationRead] = []


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    message: ChatMessageRead


class ConversationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    created_at: datetime


class ConversationDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    created_at: datetime
    messages: list[ChatMessageRead] = []
