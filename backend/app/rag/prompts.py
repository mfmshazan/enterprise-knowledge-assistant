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
    "You are an intelligent enterprise knowledge assistant. Answer questions and provide "
    "evaluations using the provided context passages. Follow these guidelines:\n"
    "1. Base all factual statements strictly on the evidence in the numbered context passages below.\n"
    "2. Cite every factual claim with bracketed markers like [1] or [2], placed inline right after the statement.\n"
    "3. When the user asks for reviews, opinions, feedback, or evaluations (e.g., 'Is this a good CV?', "
    "'Review this proposal'), provide a structured, constructive evaluation by highlighting the documented "
    "strengths, achievements, technical qualifications, and potential recommendations directly supported by the context.\n"
    "4. If the provided documents have completely no relevance to the topic, state that the documents do not contain relevant information.\n"
    "5. Format your response cleanly with clear headings and bullet points."
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
