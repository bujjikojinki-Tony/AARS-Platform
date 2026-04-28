from __future__ import annotations

from weather_comparison_engine.opportunity_board.opportunity_policy_loader import policy_ref


def build_opportunity_score(row: dict, context: dict | None = None) -> tuple[float, str]:
    details = build_opportunity_score_details(row, context)
    return details["opportunity_score"], details["opportunity_reason"]


def build_opportunity_score_details(row: dict, context: dict | None = None) -> dict:
    context = context or {}
    policy_bundle = context.get("opportunity_policy_bundle") or {}
    scoring_policy = policy_bundle.get("opportunity_scoring_policy") or {}
    freshness_policy = policy_bundle.get("freshness_mapping_policy") or {}
    source_precision_policy = policy_bundle.get("source_precision_policy") or {}
    confidence_gap = _to_float(row.get("confidence_adjusted_gap")) or 0.0
    comparison_status = str(row.get("comparison_status") or "").lower()
    freshness_status = str(row.get("freshness_status") or context.get("freshness_status") or "").lower()
    source_precision_score = _score_source_precision(row, source_precision_policy)
    alert_count = int(row.get("alert_count") or 0)
    anomaly_count = int(row.get("anomaly_count") or 0)
    market_lag_score = _score_market_lag(comparison_status)
    freshness_score = _score_freshness(freshness_status, freshness_policy)
    alert_density_score = min(alert_count / 3.0, 1.0)
    anomaly_density_score = min(anomaly_count / 3.0, 1.0)
    edge_score = min(abs(confidence_gap) * 2.5, 1.0)
    if edge_score <= 0.0 and row.get("initial_edge_label") is not None:
        edge_score = _score_initial_edge_label(row.get("initial_edge_label"))

    components = {
        "edge_component": edge_score,
        "market_lag_component": market_lag_score,
        "source_precision_component": source_precision_score,
        "freshness_component": freshness_score,
        "liquidity_component": alert_density_score,
        "anomaly_penalty_component": anomaly_density_score,
    }
    weights = scoring_policy.get("weights") or {
        "edge_component": 0.24,
        "market_lag_component": 0.16,
        "source_precision_component": 0.16,
        "freshness_component": 0.12,
        "liquidity_component": 0.16,
        "anomaly_penalty_component": 0.16,
    }
    score = sum(float(weights.get(key, 0.0) or 0.0) * float(value or 0.0) for key, value in components.items())
    score = round(max(0.0, min(1.0, score)), 4)
    reason = (
        f"edge={edge_score:.2f};lag={market_lag_score:.2f};"
        f"alerts={alert_density_score:.2f};anomalies={anomaly_density_score:.2f};"
        f"precision={source_precision_score:.2f};freshness={freshness_score:.2f}"
    )
    return {
        "opportunity_score": score,
        "opportunity_reason": reason,
        "opportunity_components": {
            "edge_component": round(edge_score, 4),
            "market_lag_component": round(market_lag_score, 4),
            "source_precision_component": round(source_precision_score, 4),
            "freshness_component": round(freshness_score, 4),
            "liquidity_component": round(alert_density_score, 4),
            "anomaly_penalty_component": round(anomaly_density_score, 4),
        },
        "opportunity_policy_ref": policy_ref(scoring_policy, "opportunity_scoring_policy.default"),
        "scoring_policy_ref": policy_ref(scoring_policy, "opportunity_scoring_policy.default"),
        "freshness_mapping_policy_ref": policy_ref(freshness_policy, "freshness_mapping_policy.default"),
        "source_precision_policy_ref": policy_ref(source_precision_policy, "source_precision_policy.default"),
    }


def _score_market_lag(comparison_status: str) -> float:
    mapping = {
        "aligned": 0.55,
        "mild_divergence": 0.75,
        "strong_divergence": 0.92,
        "unknown": 0.35,
        "unmatched_rule": 0.25,
        "blocked": 0.15,
    }
    return mapping.get(comparison_status, 0.45)


def _score_freshness(status: str, policy: dict | None = None) -> float:
    mapping = (policy or {}).get("mapping") or {
        "fresh": 1.0,
        "healthy": 1.0,
        "pass": 1.0,
        "warm": 0.72,
        "warning": 0.72,
        "seed_prior": 0.55,
        "stale": 0.35,
        "blocked": 0.15,
        "unavailable": 0.15,
        "unknown": 0.4,
    }
    return mapping.get(status, 0.5)


def _score_source_precision(row: dict, policy: dict | None = None) -> float:
    grade = str(row.get("source_match_grade") or "").lower()
    official_vs_proxy = str(row.get("official_vs_proxy_source") or "").lower()
    resolver_confidence = _to_float(row.get("resolver_confidence")) or 0.0
    combination_scores = (policy or {}).get("combination_scores") or {}
    combination_key = f"{grade}:{official_vs_proxy}"
    if combination_key in combination_scores:
        return max(0.0, min(1.0, round(float(combination_scores.get(combination_key) or 0.0), 4)))
    mapping = (policy or {}).get("match_grade_scores") or {
        "exact_station": 1.0,
        "family_exact": 0.82,
        "family_only": 0.55,
        "unmatched": 0.25,
        "": 0.3,
        "unknown": 0.3,
    }
    base = mapping.get(grade, 0.45)
    adjustments = (policy or {}).get("officialness_adjustments") or {"official": 0.08, "proxy": -0.08}
    base += float(adjustments.get(official_vs_proxy, 0.0) or 0.0)
    base += min(max(resolver_confidence, 0.0), 1.0) * float((policy or {}).get("resolver_confidence_weight", 0.12) or 0.0)
    return max(0.0, min(1.0, round(base, 4)))


def _score_initial_edge_label(value: object) -> float:
    try:
        return max(0.0, min(1.0, float(value) / 5.0))
    except Exception:
        return 0.0


def _to_float(value: object) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        return float(value)
    except Exception:
        return None
