"""Unit tests for the recursive text chunker."""

from __future__ import annotations

from app.ingestion.chunker import TextChunker, estimate_tokens


def test_empty_text_yields_no_chunks() -> None:
    assert TextChunker(100, 20).split_text("   ") == []


def test_short_text_is_a_single_chunk() -> None:
    chunks = TextChunker(100, 20).split_text("Just a short sentence.")
    assert chunks == ["Just a short sentence."]


def test_long_text_splits_into_multiple_chunks_under_size() -> None:
    text = "\n\n".join(f"Paragraph number {i} with some filler words here." for i in range(50))
    chunks = TextChunker(200, 40).split_text(text)
    assert len(chunks) > 1
    # Chunks should generally respect the size budget (allow a little slack).
    assert all(len(c) <= 260 for c in chunks)


def test_adjacent_chunks_overlap() -> None:
    words = " ".join(f"w{i}" for i in range(300))
    chunks = TextChunker(120, 40).split_text(words)
    assert len(chunks) >= 2
    # The tail of one chunk should reappear at the head of the next.
    first_tail = chunks[0].split()[-3:]
    assert any(w in chunks[1] for w in first_tail)


def test_overlap_must_be_smaller_than_size() -> None:
    import pytest

    with pytest.raises(ValueError, match="smaller"):
        TextChunker(100, 100)


def test_estimate_tokens() -> None:
    assert estimate_tokens("") == 1
    assert estimate_tokens("a" * 40) == 10
