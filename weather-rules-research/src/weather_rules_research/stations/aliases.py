from __future__ import annotations

import re
import unicodedata


_BUILTIN_ALIASES = {
    "nyc": "new york",
    "new york city": "new york",
    "phx": "phoenix",
    "la": "los angeles",
}


def canonicalize_location_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    collapsed = re.sub(r"\s+", " ", ascii_text.strip().lower())
    return collapsed


def normalize_location_alias(value: str) -> str:
    canonical = canonicalize_location_name(value)
    return _BUILTIN_ALIASES.get(canonical, canonical)
