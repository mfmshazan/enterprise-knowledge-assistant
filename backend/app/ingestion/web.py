"""Single-page URL ingestion: fetch a web page and extract readable text.

Scope note: this fetches ONE page, not a recursive crawl. It strips scripts,
styles, and navigation chrome with BeautifulSoup and returns the visible text.
Full crawling (link following, robots.txt, politeness delays, depth limits) is a
later enhancement.
"""

from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.exceptions import ValidationError

# Tags whose contents are not human-readable body text.
_NOISE_TAGS = ["script", "style", "noscript", "template", "svg"]


async def fetch_url_text(url: str) -> tuple[str, str | None]:
    """Return (text, page_title) for a URL, or raise ValidationError on failure."""
    try:
        async with httpx.AsyncClient(
            timeout=settings.URL_FETCH_TIMEOUT, follow_redirects=True
        ) as client:
            response = await client.get(url, headers={"User-Agent": "EKA-Ingestion/0.1"})
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ValidationError(f"Failed to fetch URL: {exc}") from exc

    return extract_html_text(response.text)


def extract_html_text(html: str) -> tuple[str, str | None]:
    """Parse HTML into (readable_text, title). Pure function -> easy to test."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(_NOISE_TAGS):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else None
    # `separator="\n"` keeps block structure so the chunker can split on it.
    text = soup.get_text(separator="\n")
    # Collapse runs of blank lines produced by removed tags.
    lines = [line.strip() for line in text.splitlines()]
    cleaned = "\n".join(line for line in lines if line)
    return cleaned, title
