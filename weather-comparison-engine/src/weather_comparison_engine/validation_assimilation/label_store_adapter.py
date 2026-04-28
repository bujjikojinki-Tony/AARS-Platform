from __future__ import annotations

from typing import Any


def adapt_label_store_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    adapted: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        adapted.append(
            {
                "market_id": row.get("market_id"),
                "market_family": row.get("market_family"),
                "truth_label": row.get("truth_label") or row.get("label"),
                "truth_value": row.get("truth_value"),
                "truth_source_name": row.get("truth_source_name") or row.get("source") or "official",
                "official_vs_proxy_source": row.get("official_vs_proxy_source") or "official",
                "source_match_grade": row.get("source_match_grade") or "exact_station",
                "label_generated_at": row.get("label_generated_at") or row.get("generated_at"),
                "label_version": row.get("label_version") or "v1",
                "can_replay": True,
            }
        )
    return adapted
