from __future__ import annotations

from weather_comparison_engine.opportunity_board.opportunity_policy_loader import policy_ref


def recommend_best_model(row: dict, context: dict | None = None) -> tuple[str, list[str], str]:
    details = recommend_best_model_details(row, context)
    return details["best_model"], details["best_source_stack"], details["best_model_reason"]


def recommend_best_model_details(row: dict, context: dict | None = None) -> dict:
    context = context or {}
    family = str(row.get("market_family") or "").lower()
    market_question = str(row.get("market_question") or "").strip()
    validation = context.get("model_validation_report") or {}
    policy = (context.get("opportunity_policy_bundle") or {}).get("model_recommendation_policy") or {}
    family_candidates = policy.get("family_candidates") or {}
    rollout = validation.get("family_rollout_summary") or {}
    top_family = str(rollout.get("top_family") or "").lower()

    if row.get("seeded_from_manual_research") and row.get("best_model"):
        model = str(row.get("best_model"))
        source_stack = [str(item) for item in row.get("best_source_stack") or []] or ["resolver_registry"]
        reason = "manual opportunity seed provides a cold-start best model prior; system scoring should supersede it when enough live evidence is available"
    elif family in family_candidates:
        candidate = family_candidates.get(family) or {}
        model = str(candidate.get("best_model") or "Resolver Recommended")
        source_stack = [str(item) for item in candidate.get("best_source_stack") or []] or ["resolver_registry"]
        reason = str(candidate.get("reason") or "model recommendation policy selected this family stack")
    elif "temperature" in family:
        model = "ECMWF"
        source_stack = ["ecmwf", "metar", "official_obs"]
        reason = "temperature-family baseline favors ECMWF and exact-station observations"
    elif family == "sea_ice_extent":
        model = "Sea Ice Dataset"
        source_stack = ["sea_ice_dataset", "official_obs"]
        reason = "sea-ice family favors the official climate dataset"
    elif family == "global_temperature_index":
        model = "Climate Index Baseline"
        source_stack = ["climate_index_source", "official_obs"]
        reason = "global index family favors the official climate index source"
    elif top_family and top_family == family:
        model = str(validation.get("best_model") or "Validation Best Model")
        source_stack = [str(item) for item in validation.get("best_source_stack") or []] or ["resolver_registry"]
        reason = "validation summary currently recommends this family stack"
    else:
        model = str(row.get("best_model") or context.get("best_model") or "Resolver Recommended")
        source_stack = [str(item) for item in row.get("best_source_stack") or []]
        if not source_stack:
            source_stack = ["resolver_registry", "forecast_snapshot", "observation_snapshot"]
        reason = f"fallback recommendation derived from market question `{market_question}`"

    return {
        "best_model": model,
        "best_source_stack": source_stack,
        "best_model_reason": reason,
        "best_model_components": {
            "family_fit": 1.0 if "temperature" in family or family in {"sea_ice_extent", "global_temperature_index"} else 0.6,
            "source_availability": 0.8,
            "source_precision_fit": 0.9 if "temperature" in family else 0.7,
            "freshness_reliability": 0.85,
            "validation_support": 0.8 if top_family and top_family == family else 0.6,
        },
        "model_recommendation_policy_ref": policy_ref(policy, "model_recommendation_policy.default"),
    }
