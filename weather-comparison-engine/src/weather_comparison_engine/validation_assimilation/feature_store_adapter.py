from __future__ import annotations

from typing import Any


CANONICAL_FIELDS = (
    "market_id",
    "market_family",
    "market_question",
    "location_name",
    "target_date",
    "variable_name",
    "market_probability",
    "fair_value",
    "edge",
    "confidence_adjusted_gap",
    "band_distance",
    "source_match_grade",
    "official_vs_proxy_source",
    "precision_policy_ref",
    "rounding_policy_ref",
    "band_mapping_policy_ref",
    "normalization_version",
)


def adapt_feature_store_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    adapted: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        payload = {field: row.get(field) for field in CANONICAL_FIELDS if row.get(field) is not None}
        payload["input_mode"] = "canonical_only"
        adapted.append(payload)
    return adapted
