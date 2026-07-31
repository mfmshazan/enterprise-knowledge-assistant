"""Tiny slug helper.

Turns a display name ("Acme, Inc.") into a URL-safe handle ("acme-inc"). Kept
dependency-free (no external slugify lib) because our needs are simple. Slugs are
used as stable, human-readable identifiers for organizations in URLs.
"""

from __future__ import annotations

import re
import unicodedata

_NON_WORD = re.compile(r"[^\w]+")
_DASHES = re.compile(r"-{2,}")


def slugify(value: str, *, fallback: str = "workspace") -> str:
    # Normalize accents to ASCII (café -> cafe), then lowercase.
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = _NON_WORD.sub("-", normalized.lower()).strip("-")
    slug = _DASHES.sub("-", slug)
    return slug or fallback
