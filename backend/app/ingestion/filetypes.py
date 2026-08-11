"""Supported file formats and detection.

We accept a small, well-understood set of document formats. Detection is by file
extension (authoritative here) with the browser-provided content type kept for
storage metadata. Anything outside the allowlist is rejected at the API boundary
so the pipeline only ever sees formats it can actually extract text from.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import PurePosixPath


class DocFormat(StrEnum):
    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "markdown"
    TEXT = "text"


_EXTENSION_MAP: dict[str, DocFormat] = {
    ".pdf": DocFormat.PDF,
    ".docx": DocFormat.DOCX,
    ".md": DocFormat.MARKDOWN,
    ".markdown": DocFormat.MARKDOWN,
    ".txt": DocFormat.TEXT,
}

# Human-readable list for error messages.
SUPPORTED_EXTENSIONS = sorted(_EXTENSION_MAP)


def detect_format(filename: str) -> DocFormat | None:
    """Return the DocFormat for a filename, or None if unsupported."""
    suffix = PurePosixPath(filename).suffix.lower()
    return _EXTENSION_MAP.get(suffix)
