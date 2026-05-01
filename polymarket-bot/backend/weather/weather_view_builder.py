from statistics import mean
from uuid import uuid4

from backend.models.weather import EvidenceFreshness
from backend.models.weather import EvidencePack
from backend.models.weather import ParseConfidence
from backend.models.weather import WeatherView


class WeatherViewBuilder:
    def __init__(self, default_sigma: float = 2.5):
        self.default_sigma = default_sigma

    def build(self, pack: EvidencePack) -> WeatherView:
        values = [
            source.normalized_value
            for source in pack.sources
            if source.normalized_value is not None
        ]
        if not values:
            raise ValueError("cannot build WeatherView without normalized source values")

        expected_value = mean(values)
        sigma = self.default_sigma
        confidence = self._resolve_confidence(pack, len(values))
        return WeatherView(
            weather_view_id=f"wv_{uuid4().hex[:10]}",
            evidence_pack_id=pack.evidence_pack_id,
            market_id=pack.market_id,
            city=pack.descriptor.city,
            target_date=pack.descriptor.target_date,
            expected_value=expected_value,
            expected_range_low=expected_value - sigma,
            expected_range_high=expected_value + sigma,
            sigma=sigma,
            threshold=pack.descriptor.threshold,
            direction=pack.descriptor.direction,
            unit=pack.descriptor.unit,
            confidence=confidence,
            evidence_summary=self._build_summary(pack, expected_value),
            invalidation_rules=self._build_invalidation_rules(pack, expected_value),
            confirmation_rules=self._build_confirmation_rules(pack, expected_value),
        )

    def _resolve_confidence(self, pack: EvidencePack, value_count: int) -> ParseConfidence:
        if (
            pack.evidence_freshness == EvidenceFreshness.FRESH
            and value_count >= 2
            and pack.evidence_conflict_level.value in {"NONE", "LOW"}
        ):
            return ParseConfidence.HIGH
        if pack.evidence_freshness in {EvidenceFreshness.FRESH, EvidenceFreshness.PARTIAL}:
            return ParseConfidence.MEDIUM
        return ParseConfidence.LOW

    def _build_summary(self, pack: EvidencePack, expected_value: float) -> list[str]:
        unit = pack.descriptor.unit.value
        items = [
            f"{source.source_name}: normalized value = {source.normalized_value}{unit}"
            for source in pack.sources
            if source.normalized_value is not None
        ]
        items.append(f"Expected value = {round(expected_value, 2)}{unit}")
        return items

    def _build_invalidation_rules(self, pack: EvidencePack, expected_value: float) -> list[str]:
        threshold = pack.descriptor.threshold
        unit = pack.descriptor.unit.value
        if threshold is None:
            return ["Invalidate if threshold cannot be resolved."]
        return [
            f"Invalidate if updated expected value moves more than 2.5{unit} away from {round(expected_value, 2)}{unit}.",
            "Invalidate if all primary sources become stale or missing.",
            "Invalidate if evidence conflict level becomes HIGH.",
        ]

    def _build_confirmation_rules(self, pack: EvidencePack, expected_value: float) -> list[str]:
        threshold = pack.descriptor.threshold
        unit = pack.descriptor.unit.value
        if threshold is None:
            return ["Confirm only after threshold is resolved."]
        return [
            "Confirm if at least one primary source remains fresh.",
            f"Confirm if expected value stays near {round(expected_value, 2)}{unit}.",
            f"Confirm against market threshold {threshold}{unit}.",
        ]
