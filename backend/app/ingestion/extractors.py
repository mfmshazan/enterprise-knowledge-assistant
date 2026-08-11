"""Text extraction — turn raw bytes of a supported format into plain text.

One function per format, dispatched by `DocFormat`. These are synchronous and
CPU-bound (pypdf/python-docx parse in-process), so the pipeline calls them via
`anyio.to_thread.run_sync` to keep the event loop free.

We normalize whitespace lightly but otherwise preserve the document's text as-is;
cleaning/segmentation is the chunker's job, not the extractor's.
"""

from __future__ import annotations

import io

from docx import Document as DocxDocument
from pypdf import PdfReader

from app.ingestion.filetypes import DocFormat


def _extract_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)


def _extract_docx(data: bytes) -> str:
    document = DocxDocument(io.BytesIO(data))
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def _extract_plaintext(data: bytes) -> str:
    # errors="replace" so a stray byte never crashes ingestion.
    return data.decode("utf-8", errors="replace")


def extract_text(fmt: DocFormat, data: bytes) -> str:
    """Extract plain text from `data` for the given format."""
    if fmt is DocFormat.PDF:
        return _extract_pdf(data)
    if fmt is DocFormat.DOCX:
        return _extract_docx(data)
    # Markdown and plain text are already text; keep markdown syntax as content.
    return _extract_plaintext(data)
