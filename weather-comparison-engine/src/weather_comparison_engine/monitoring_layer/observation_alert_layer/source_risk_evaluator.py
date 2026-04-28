from __future__ import annotations


def build_source_risk_result(*, market_rule: dict, forecast_snapshot: dict | None = None) -> dict:
    forecast_snapshot = forecast_snapshot or {}
    source_match_grade = _string_value(
        market_rule.get("source_match_grade")
        or forecast_snapshot.get("source_match_grade")
        or "unknown"
    )
    official_vs_proxy_source = _string_value(
        market_rule.get("official_vs_proxy_source")
        or forecast_snapshot.get("official_vs_proxy_source")
        or "unknown"
    )
    freshness_status = _string_value(
        market_rule.get("freshness_status")
        or forecast_snapshot.get("freshness_status")
        or "unknown"
    )
    return {
        "source_match_risk": _match_risk(source_match_grade),
        "officialness_risk": _officialness_risk(official_vs_proxy_source),
        "freshness_risk": _freshness_risk(freshness_status),
    }


def _match_risk(grade: str) -> str:
    if grade in {"exact_station", "family_exact"}:
        return "low"
    if grade in {"family_only", "family_level"}:
        return "medium"
    return "high"


def _officialness_risk(value: str) -> str:
    if value == "official":
        return "low"
    if value == "proxy":
        return "medium"
    return "high"


def _freshness_risk(value: str) -> str:
    if value == "fresh":
        return "low"
    if value in {"stale", "delayed"}:
        return "medium"
    return "high"


def _string_value(value: object) -> str:
    return str(value).strip() if value not in (None, "") else ""
