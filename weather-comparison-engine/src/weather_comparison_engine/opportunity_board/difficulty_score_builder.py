from __future__ import annotations

from weather_comparison_engine.opportunity_board.opportunity_policy_loader import policy_ref


def build_difficulty_score(row: dict) -> tuple[float, str, str]:
    details = build_difficulty_score_details(row)
    return details["difficulty_score"], details["difficulty_label"], details["difficulty_reason"]


def build_difficulty_score_details(row: dict, context: dict | None = None) -> dict:
    context = context or {}
    policy = (context.get("opportunity_policy_bundle") or {}).get("difficulty_scoring_policy") or {}
    source_match_grade = str(row.get("source_match_grade") or "").lower()
    official_vs_proxy = str(row.get("official_vs_proxy_source") or "").lower()
    freshness_status = str(row.get("freshness_status") or "").lower()
    resolver_confidence = _to_float(row.get("resolver_confidence")) or 0.0
    family = str(row.get("market_family") or "").lower()
    initial_difficulty_label = str(row.get("initial_difficulty_label") or "").lower()

    source_component = {
        "exact_station": 0.12,
        "family_exact": 0.34,
        "family_only": 0.58,
        "unmatched": 0.82,
        "": 0.65,
    }.get(source_match_grade, 0.5)
    official_component = 0.16 if official_vs_proxy == "official" else 0.44 if official_vs_proxy == "proxy" else 0.3
    freshness_component = {
        "fresh": 0.1,
        "healthy": 0.1,
        "warm": 0.32,
        "warning": 0.32,
        "seed_prior": {
            "easy": 0.28,
            "medium": 0.45,
            "hard": 0.68,
        }.get(initial_difficulty_label, 0.45),
        "stale": 0.72,
        "blocked": 0.9,
        "unavailable": 0.9,
        "unknown": 0.45,
    }.get(freshness_status, 0.4)
    resolver_component = 1.0 - min(max(resolver_confidence, 0.0), 1.0)
    family_component = {
        "station_temperature": 0.24,
        "global_temperature_index": 0.42,
        "sea_ice_extent": 0.54,
        "weather_metric.precipitation": 0.46,
        "weather_metric.wind_speed": 0.46,
        "weather_metric.snowfall": 0.5,
    }.get(family, 0.36)

    components = {
        "source_precision_difficulty": source_component,
        "resolver_stability_difficulty": resolver_component,
        "settlement_clarity_difficulty": official_component,
        "freshness_reliability_difficulty": freshness_component,
        "market_complexity_difficulty": family_component,
    }
    weights = policy.get("weights") or {
        "source_precision_difficulty": 0.28,
        "settlement_clarity_difficulty": 0.2,
        "freshness_reliability_difficulty": 0.22,
        "resolver_stability_difficulty": 0.15,
        "market_complexity_difficulty": 0.15,
    }
    score = sum(float(weights.get(key, 0.0) or 0.0) * float(value or 0.0) for key, value in components.items())
    score = round(max(0.0, min(1.0, score)), 4)
    thresholds = policy.get("label_thresholds") or {}
    easy_max = float(thresholds.get("easy_max", 0.33) or 0.33)
    medium_max = float(thresholds.get("medium_max", 0.66) or 0.66)
    if score <= easy_max:
        label = "easy"
    elif score <= medium_max:
        label = "medium"
    else:
        label = "hard"
    reason = (
        f"source={source_component:.2f};official={official_component:.2f};"
        f"freshness={freshness_component:.2f};resolver={resolver_component:.2f};family={family_component:.2f}"
    )
    return {
        "difficulty_score": score,
        "difficulty_label": label,
        "difficulty_reason": reason,
        "difficulty_components": {
            "source_precision_difficulty": round(source_component, 4),
            "resolver_stability_difficulty": round(resolver_component, 4),
            "settlement_clarity_difficulty": round(official_component, 4),
            "freshness_reliability_difficulty": round(freshness_component, 4),
            "market_complexity_difficulty": round(family_component, 4),
        },
        "difficulty_policy_ref": policy_ref(policy, "difficulty_scoring_policy.default"),
    }


def _to_float(value: object) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        return float(value)
    except Exception:
        return None
