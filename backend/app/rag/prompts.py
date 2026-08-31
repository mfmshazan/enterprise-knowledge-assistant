"""Prompt construction for grounded RAG answers.

The system prompt is the primary defense against hallucination: it instructs the
model to answer *only* from the supplied context, to cite sources with [n]
markers that map to the numbered context blocks, and to admit when the answer
isn't present rather than inventing one. The retrieved chunks are formatted as a
numbered list so the [n] citations are unambiguous.
"""

from __future__ import annotations

from app.llm.base import ChatMessage
from app.services.retrieval_service import RetrievedChunk

SYSTEM_PROMPT = (
    "You are a knowledge assistant that answers questions using ONLY the provided "
    "context. Follow these rules strictly:\n"
    "1. Base your answer solely on the numbered context passages below. Do not use "
    "outside knowledge.\n"
    "2. Cite the passages you rely on with bracketed markers like [1] or [2], placed "
    "inline right after the relevant statement.\n"
    "3. If the context does not contain the answer, say you don't have enough "
    "information in the provided documents — do not guess.\n"
    "4. Be concise and factual."
)

_NO_CONTEXT_NOTE = (
    "No relevant passages were found in the knowledge base for this question. "
    "Tell the user you don't have information about it in the available documents."
)


def build_grounded_messages(question: str, chunks: list[RetrievedChunk]) -> list[ChatMessage]:
    if chunks:
        blocks = "\n\n".join(
            f"[{i}] (source: {chunk.document_title})\n{chunk.content}"
            for i, chunk in enumerate(chunks, start=1)
        )
        context_section = f"Context passages:\n{blocks}"
    else:
        context_section = _NO_CONTEXT_NOTE

    user_content = f"{context_section}\n\nQuestion: {question}"
    return [
        ChatMessage(role="system", content=SYSTEM_PROMPT),
        ChatMessage(role="user", content=user_content),
    ]
