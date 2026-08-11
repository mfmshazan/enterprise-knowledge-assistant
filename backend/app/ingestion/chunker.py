"""Recursive character text splitter with overlap.

Why chunk at all? Embedding models have a bounded context and retrieval works
best on focused passages, so a long document is split into ~`chunk_size`-char
pieces. We split on progressively finer separators (paragraph → line → sentence →
word) so boundaries fall at natural places instead of mid-word. Adjacent chunks
**overlap** by `chunk_overlap` chars so a fact spanning a boundary still appears
whole in at least one chunk — the single biggest lever on retrieval recall.

This mirrors LangChain's RecursiveCharacterTextSplitter but is dependency-free
and small enough to read in one sitting.
"""

from __future__ import annotations

_DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars/token) — good enough for metadata/budgeting."""
    return max(1, len(text) // 4)


class TextChunker:
    def __init__(
        self,
        chunk_size: int,
        chunk_overlap: int,
        separators: list[str] | None = None,
    ) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size.")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or _DEFAULT_SEPARATORS

    def split_text(self, text: str) -> list[str]:
        text = text.strip()
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, text: str, separators: list[str]) -> list[str]:
        final: list[str] = []

        # Pick the coarsest separator that actually occurs in the text.
        separator = separators[-1]
        remaining = separators[-1:]
        for i, sep in enumerate(separators):
            if sep == "":
                separator = ""
                remaining = []
                break
            if sep in text:
                separator = sep
                remaining = separators[i + 1 :]
                break

        splits = list(text) if separator == "" else text.split(separator)

        good: list[str] = []
        for piece in splits:
            if len(piece) < self.chunk_size:
                good.append(piece)
                continue
            # Piece too big: flush what we have, then recurse into it.
            if good:
                final.extend(self._merge(good, separator))
                good = []
            if remaining:
                final.extend(self._split(piece, remaining))
            else:
                final.append(piece)
        if good:
            final.extend(self._merge(good, separator))
        return final

    def _merge(self, splits: list[str], separator: str) -> list[str]:
        sep_len = len(separator)
        chunks: list[str] = []
        current: list[str] = []
        total = 0

        for piece in splits:
            addition = len(piece) + (sep_len if current else 0)
            if total + addition > self.chunk_size and current:
                joined = separator.join(current).strip()
                if joined:
                    chunks.append(joined)
                # Slide the window forward, keeping ~chunk_overlap chars of tail.
                while total > self.chunk_overlap and current:
                    total -= len(current[0]) + (sep_len if len(current) > 1 else 0)
                    current.pop(0)
            current.append(piece)
            total += len(piece) + (sep_len if len(current) > 1 else 0)

        joined = separator.join(current).strip()
        if joined:
            chunks.append(joined)
        return chunks
