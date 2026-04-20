from __future__ import annotations

import re
from datetime import datetime, timezone

from weather_comparison_engine.schemas.probability_state import ProbabilityState


class ShadowProbabilityEngine:
    """Heuristic fair-value estimate for visibility only.

    This is intentionally conservative and explicitly not calibrated. It gives the
    dashboard a stable shadow signal while later phases build a proper training and
    validation layer.
    """

    def build_probability_state(
        self,
        *,
        market_snapshot: dict,
        forecast_snapshot: dict | None,
        resolver_rule: dict | None,
    ) -> ProbabilityState:
        market_id = str(market_snapshot.get("market_id") or "")
        market_probability = _to_float(market_snapshot.get("market_probability"))
        resolver_status = (resolver_rule or {}).get("resolver_status")
        model_band = (forecast_snapshot or {}).get("model_band")
        market_band = market_snapshot.get("market_band")
        expected_band = (resolver_rule or {}).get("expected_band")
        forecast_market_id = str((forecast_snapshot or {}).get("market_id") or "")
        forecast_confidence = _to_float((forecast_snapshot or {}).get("confidence_score")) or 0.0
        resolver_confidence = _to_float((resolver_rule or {}).get("resolver_confidence")) or 0.0
        confidence = round(max(0.0, min(1.0, forecast_confidence * max(resolver_confidence, 0.5))), 4)

        if not market_id:
            return self._blocked_state(
                market_id="-",
                market_snapshot=market_snapshot,
                resolver_rule=resolver_rule,
                market_probability=market_probability,
                confidence=0.0,
                reason="missing_market_id",
            )

        if resolver_status != "matched":
            return self._blocked_state(
                market_id=market_id,
                market_snapshot=market_snapshot,
                resolver_rule=resolver_rule,
                market_probability=market_probability,
                confidence=0.0,
                reason=f"resolver_status={resolver_status or 'missing'}",
            )

        if forecast_market_id and forecast_market_id != market_id:
            return self._blocked_state(
                market_id=market_id,
                market_snapshot=market_snapshot,
                resolver_rule=resolver_rule,
                market_probability=market_probability,
                confidence=confidence,
                reason=f"forecast_market_mismatch:{forecast_market_id}",
            )

        support_score, reason = self._support_score(
            model_band=str(model_band) if model_band is not None else None,
            market_band=str(market_band) if market_band is not None else None,
            expected_band=str(expected_band) if expected_band is not None else None,
        )
        model_probability = round(support_score, 4)
        fair_value = model_probability
        edge = _subtract(fair_value, market_probability)
        confidence_adjusted_edge = (
            round(edge * confidence, 4) if edge is not None and confidence is not None else None
        )

        return ProbabilityState(
            market_id=market_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            market_implied_probability=market_probability,
            model_probability=model_probability,
            fair_value=fair_value,
            forecast_support_score=round(support_score, 4),
            confidence=confidence,
            edge=edge,
            confidence_adjusted_edge=confidence_adjusted_edge,
            resolver_status=resolver_status,
            resolver_reason=(resolver_rule or {}).get("resolver_reason"),
            market_family=(resolver_rule or {}).get("market_family"),
            required_data_source=(resolver_rule or {}).get("required_data_source"),
            band_scheme=(resolver_rule or {}).get("band_scheme"),
            market_band=str(market_band) if market_band is not None else None,
            model_band=str(model_band) if model_band is not None else None,
            expected_band=str(expected_band) if expected_band is not None else None,
            probability_reason=reason,
        )

    def _blocked_state(
        self,
        *,
        market_id: str,
        market_snapshot: dict,
        resolver_rule: dict | None,
        market_probability: float | None,
        confidence: float,
        reason: str,
    ) -> ProbabilityState:
        return ProbabilityState(
            market_id=market_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            market_implied_probability=market_probability,
            confidence=confidence,
            resolver_status=(resolver_rule or {}).get("resolver_status"),
            resolver_reason=(resolver_rule or {}).get("resolver_reason"),
            market_family=(resolver_rule or {}).get("market_family") or market_snapshot.get("market_family"),
            required_data_source=(resolver_rule or {}).get("required_data_source"),
            band_scheme=(resolver_rule or {}).get("band_scheme") or market_snapshot.get("market_band_scheme"),
            market_band=market_snapshot.get("market_band"),
            expected_band=(resolver_rule or {}).get("expected_band"),
            probability_reason=reason,
        )

    def _support_score(
        self,
        *,
        model_band: str | None,
        market_band: str | None,
        expected_band: str | None,
    ) -> tuple[float, str]:
        target_band = expected_band or market_band
        if not model_band or not target_band:
            return 0.5, "missing_model_or_target_band"
        if model_band == target_band:
            return 0.72, "model_band_matches_target_band"

        ordinal_distance = _top_band_distance(model_band, target_band)
        if ordinal_distance is not None:
            score = max(0.05, 0.72 - 0.16 * ordinal_distance)
            return score, f"ordinal_band_distance={ordinal_distance}"

        return 0.42, f"model_band={model_band};target_band={target_band}"


def _top_band_distance(a: str, b: str) -> int | None:
    a_match = re.match(r"^top_(\d+)$", a)
    b_match = re.match(r"^top_(\d+)$", b)
    if not a_match or not b_match:
        return None
    return abs(int(a_match.group(1)) - int(b_match.group(1)))


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _subtract(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return round(a - b, 4)

