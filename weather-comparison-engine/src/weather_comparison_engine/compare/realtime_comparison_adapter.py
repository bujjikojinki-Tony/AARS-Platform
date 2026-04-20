from __future__ import annotations

from datetime import datetime, timezone

from weather_comparison_engine.compare.band_compare import BandCompare
from weather_comparison_engine.compare.confidence_compare import ConfidenceCompare
from weather_comparison_engine.compare.divergence_tracker import DivergenceTracker


class RealtimeComparisonAdapter:
    def __init__(self) -> None:
        self.band_compare = BandCompare()
        self.confidence_compare = ConfidenceCompare()
        self.divergence_tracker = DivergenceTracker()

    def build_comparison_point(
        self,
        market_snapshot: dict,
        forecast_snapshot: dict,
        market_id: str,
        market_band: str | None,
        confidence_score: float,
        action_hint: str = "watch",
    ) -> dict:
        rule_status = forecast_snapshot.get("rule_status")
        rule_market_id = forecast_snapshot.get("rule_market_id")
        market_family = forecast_snapshot.get("market_family")
        resolution_scope = forecast_snapshot.get("resolution_scope")
        supported_by_current_pipeline = forecast_snapshot.get("supported_by_current_pipeline")
        required_data_source = forecast_snapshot.get("required_data_source")
        band_scheme = forecast_snapshot.get("band_scheme") or market_snapshot.get("market_band_scheme")
        market_band_scheme = market_snapshot.get("market_band_scheme")
        model_band = forecast_snapshot.get("model_band")
        model_value = forecast_snapshot.get("value")
        forecast_market_id = forecast_snapshot.get("market_id")
        market_probability = market_snapshot.get("market_probability")
        favored_side = market_snapshot.get("favored_side")
        yes_price = market_snapshot.get("yes_price")
        no_price = market_snapshot.get("no_price")

        if rule_status and rule_status not in {"matched", "matched_index", "matched_snapshot"}:
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "market_id": market_id,
                "model_value": model_value,
                "model_band": model_band,
                "market_band": market_band,
                "market_probability": market_probability,
                "favored_side": favored_side,
                "yes_price": yes_price,
                "no_price": no_price,
                "confidence_score": confidence_score,
                "confidence_adjusted_gap": 0.0,
                "comparison_status": "unmatched_rule",
                "action_hint": action_hint,
                "market_snapshot_ref": market_snapshot.get("updated_at"),
                "forecast_snapshot_ref": forecast_snapshot.get("timestamp"),
                "rule_status": rule_status,
                "rule_market_id": rule_market_id,
                "market_family": market_family,
                "resolution_scope": resolution_scope,
                "supported_by_current_pipeline": supported_by_current_pipeline,
                "required_data_source": required_data_source,
                "band_scheme": band_scheme,
                "market_band_scheme": market_band_scheme,
                "comparison_reason": (
                    f"forecast rule_status={rule_status}; "
                    f"rule_market_id={rule_market_id}"
                ),
            }

        band_distance = self.band_compare.distance(
            model_band,
            market_band,
            band_scheme=band_scheme,
        )
        adjusted_gap = self.confidence_compare.adjusted_gap(
            band_distance=band_distance,
            confidence_score=confidence_score,
        )
        status = self.divergence_tracker.classify(band_distance)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "market_id": market_id,
            "model_value": model_value,
            "model_band": model_band,
            "market_band": market_band,
            "market_probability": market_probability,
            "favored_side": favored_side,
            "yes_price": yes_price,
            "no_price": no_price,
            "confidence_score": confidence_score,
            "confidence_adjusted_gap": adjusted_gap,
            "comparison_status": status,
            "action_hint": action_hint,
            "market_snapshot_ref": market_snapshot.get("updated_at"),
            "forecast_snapshot_ref": forecast_snapshot.get("timestamp"),
            "comparison_reason": None,
            "rule_status": rule_status,
            "rule_market_id": rule_market_id,
            "market_family": market_family,
            "resolution_scope": resolution_scope,
            "supported_by_current_pipeline": supported_by_current_pipeline,
            "required_data_source": required_data_source,
            "band_scheme": band_scheme,
            "market_band_scheme": market_band_scheme,
        }
