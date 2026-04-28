from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def normalize_page_context(
    page_context: dict[str, Any] | None = None,
    *,
    source_page: str | None = None,
    target_page: str | None = None,
    selected_market_id: str | None = None,
    selected_signal_id: str | None = None,
    selected_row_id: str | None = None,
    entry_reason: str | None = None,
    entry_context: dict[str, Any] | None = None,
    upstream_refs: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    page_context = page_context if isinstance(page_context, dict) else {}
    entry_context = entry_context if isinstance(entry_context, dict) else {}
    upstream_refs = upstream_refs if isinstance(upstream_refs, dict) else {}
    return {
        "schema_version": "page_context.v1",
        "generated_at": str(page_context.get("generated_at") or now.isoformat()),
        "source_page": str(source_page or page_context.get("source_page") or "-"),
        "target_page": str(target_page or page_context.get("target_page") or "-"),
        "selected_market_id": str(selected_market_id or page_context.get("selected_market_id") or "-"),
        "selected_signal_id": str(selected_signal_id or page_context.get("selected_signal_id") or "-"),
        "selected_row_id": str(selected_row_id or page_context.get("selected_row_id") or "-"),
        "entry_reason": str(entry_reason or page_context.get("entry_reason") or "-"),
        "entry_context": _merge_dicts(entry_context, page_context.get("entry_context")),
        "upstream_refs": _merge_dicts(upstream_refs, page_context.get("upstream_refs")),
    }


def page_context_summary(page_context: dict[str, Any] | None) -> dict[str, Any]:
    page_context = page_context if isinstance(page_context, dict) else {}
    return {
        "schema_version": "page_context_summary.v1",
        "source_page": str(page_context.get("source_page") or "-"),
        "target_page": str(page_context.get("target_page") or "-"),
        "selected_market_id": str(page_context.get("selected_market_id") or "-"),
        "selected_signal_id": str(page_context.get("selected_signal_id") or "-"),
        "selected_row_id": str(page_context.get("selected_row_id") or "-"),
        "entry_reason": str(page_context.get("entry_reason") or "-"),
    }


def _merge_dicts(*values: object) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for value in values:
        if isinstance(value, dict):
            merged.update(value)
    return merged
