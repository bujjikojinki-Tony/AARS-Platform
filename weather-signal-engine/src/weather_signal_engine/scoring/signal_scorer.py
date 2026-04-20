from uuid import uuid4

from weather_signal_engine.features.confidence_features import confidence_from_components
from weather_signal_engine.models.confidence import Confidence
from weather_signal_engine.models.forecast_state import ForecastState
from weather_signal_engine.models.market_snapshot import MarketSnapshot
from weather_signal_engine.models.rule import Rule
from weather_signal_engine.models.signal_event import SignalEvent
from weather_signal_engine.scoring.action_hint import choose_action_hint
from weather_signal_engine.scoring.edge_estimator import EdgeEstimator


class SignalScorer:
    def __init__(self) -> None:
        self.edge_estimator = EdgeEstimator()

    def score(
        self,
        rule: Rule,
        forecast_state: ForecastState,
        market_snapshot: MarketSnapshot,
    ) -> SignalEvent:
        edge_direction, edge_strength, model_band = self.edge_estimator.estimate(
            model_value=forecast_state.latest_forecast_value,
            market_band=market_snapshot.favored_band,
        )

        confidence_score, reasons = confidence_from_components(
            parse_confidence=rule.parse_confidence,
            has_market_context=market_snapshot.favored_band is not None,
            run_to_run_delta=forecast_state.run_to_run_delta,
        )

        level = "high" if confidence_score >= 0.8 else "medium" if confidence_score >= 0.5 else "low"

        confidence = Confidence(
            score=confidence_score,
            level=level,
            reasons=reasons,
        )

        action_hint = choose_action_hint(
            edge_strength=edge_strength,
            confidence_score=confidence_score,
        )

        return SignalEvent(
            signal_id=f"sig_{uuid4().hex[:10]}",
            market_id=rule.market_id,
            signal_type="weather_model_edge",
            location_name=rule.location_name,
            target_date=forecast_state.target_date,
            variable_name=forecast_state.variable_name,
            model_value=forecast_state.latest_forecast_value,
            model_band=model_band,
            market_band=market_snapshot.favored_band,
            edge_direction=edge_direction,
            edge_strength=edge_strength,
            confidence=confidence,
            action_hint=action_hint,
            notes=[],
        )
