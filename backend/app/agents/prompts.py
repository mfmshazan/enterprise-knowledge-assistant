"""Prompts for the planner and verifier agents.

The generation step reuses the grounding prompt from `app.rag.prompts`; only the
planner and verifier need their own instructions. Both are written to return a
single, easily-parsed line so the graph logic stays simple and robust.
"""

from __future__ import annotations

PLANNER_SYSTEM = (
    "You are a query planner for a document search engine. Rewrite the user's "
    "question into a single, concise search query that will retrieve the most "
    "relevant passages. Return ONLY the query text, with no quotes or explanation."
)

VERIFIER_SYSTEM = (
    "You are a grounding verifier. You are given numbered context passages and a "
    "draft answer. Decide whether every claim in the draft is supported by the "
    "context. Respond with exactly one word: GROUNDED if fully supported, or "
    "NOT_GROUNDED if any claim is unsupported or the context is insufficient."
)
