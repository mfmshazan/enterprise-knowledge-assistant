"""Agentic RAG: a LangGraph multi-agent graph that plans, retrieves, generates,
and verifies an answer, retrying retrieval when the draft isn't grounded.

Exposed to the app as an `AnswerEngine` (`AgenticAnswerEngine`) so it is a drop-in
alternative to the linear pipeline, selected via `CHAT_MODE=agentic`.
"""

from app.agents.engine import AgenticAnswerEngine

__all__ = ["AgenticAnswerEngine"]
