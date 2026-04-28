from __future__ import annotations


def build_opportunity_explanation(row: dict) -> dict:
    opportunity_components = row.get("opportunity_components") or {}
    difficulty_components = row.get("difficulty_components") or {}
    best_model_components = row.get("best_model_components") or {}
    return {
        "row_id": row.get("row_id"),
        "opportunity_components": opportunity_components,
        "difficulty_components": difficulty_components,
        "best_model_components": best_model_components,
        "best_model_reason": row.get("best_model_reason") or "-",
        "recommended_action_reason": _recommended_action_reason(row),
        "policy_refs": {
            "opportunity_policy_ref": row.get("opportunity_policy_ref"),
            "scoring_policy_ref": row.get("scoring_policy_ref") or row.get("opportunity_policy_ref"),
            "difficulty_policy_ref": row.get("difficulty_policy_ref"),
            "model_recommendation_policy_ref": row.get("model_recommendation_policy_ref"),
            "action_mapping_policy_ref": row.get("action_mapping_policy_ref"),
            "freshness_mapping_policy_ref": row.get("freshness_mapping_policy_ref"),
            "source_precision_policy_ref": row.get("source_precision_policy_ref"),
        },
        "summary_line": _summary_line(row),
    }


def _recommended_action_reason(row: dict) -> str:
    action = str(row.get("recommended_action") or "").lower()
    if action == "review_gate_block":
        return "Gate is blocked, so the market should be reviewed before any workstation action."
    if action == "refresh_pipeline_inputs":
        return "Freshness or upstream inputs are degraded; refresh the pipeline before review."
    if action == "prioritize_review":
        return "High opportunity and usable source context make this a priority review candidate."
    if action == "review_hard_market":
        return "The market looks promising but structurally harder, so review before acting."
    if action == "open_workstation":
        return "Opportunity is healthy enough to open the single-market workstation."
    return "Use the board to prioritize review before any downstream action."


def _summary_line(row: dict) -> str:
    city = str(row.get("city") or "-")
    family = str(row.get("market_family") or "-")
    opp = row.get("opportunity_score")
    diff = row.get("difficulty_label") or "-"
    model = row.get("best_model") or "-"
    return f"{city} / {family}: opp={opp}; diff={diff}; best_model={model}"
