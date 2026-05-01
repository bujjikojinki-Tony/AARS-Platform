from __future__ import annotations

from uuid import uuid4

from backend.models.outcome import MarketOutcomeRecord
from backend.models.outcome import MarketOutcomeSource
from backend.models.outcome import OutcomeArchiveSummary
from backend.models.outcome import OutcomeBundle
from backend.models.outcome import OutcomeDirection
from backend.models.outcome import OutcomeMetric
from backend.models.outcome import OutcomeResolutionRecord
from backend.models.outcome import OutcomeUnit
from backend.models.outcome import ResolvedOutcome
from backend.models.outcome import ResolutionStatus
from backend.models.outcome import WeatherActualRecord
from backend.models.outcome import WeatherActualSource


class OutcomeResolverReadOnlyService:
    """Passive, read-only outcome resolver service."""

    def __init__(self, repository):
        self.repository = repository

    def save_market_outcome(
        self,
        *,
        market_id: str,
        question: str | None = None,
        source: str | MarketOutcomeSource = MarketOutcomeSource.MANUAL,
        resolved_outcome: str | ResolvedOutcome = ResolvedOutcome.UNKNOWN,
        resolution_status: str | ResolutionStatus = ResolutionStatus.UNKNOWN,
        resolved_value: float | None = None,
        notes: str | None = None,
        raw_payload: dict | None = None,
        metadata: dict | None = None,
    ) -> MarketOutcomeRecord:
        record = MarketOutcomeRecord(
            market_outcome_id=f"mor_{uuid4().hex[:12]}",
            market_id=market_id,
            question=question,
            source=self._normalize_market_source(source),
            resolved_outcome=self._normalize_resolved_outcome(resolved_outcome),
            resolution_status=self._normalize_resolution_status(resolution_status),
            resolved_value=resolved_value,
            notes=notes,
            raw_payload=raw_payload or {},
            metadata=metadata or {},
        )
        self.repository.save_market_outcome_record(record)
        return record

    def save_weather_actual(
        self,
        *,
        market_id: str,
        city: str | None = None,
        target_date: str | None = None,
        source: str | WeatherActualSource = WeatherActualSource.MANUAL,
        metric: str | OutcomeMetric = OutcomeMetric.UNKNOWN,
        unit: str | OutcomeUnit = OutcomeUnit.UNKNOWN,
        actual_value: float | None = None,
        raw_payload: dict | None = None,
        metadata: dict | None = None,
    ) -> WeatherActualRecord:
        record = WeatherActualRecord(
            weather_actual_id=f"war_{uuid4().hex[:12]}",
            market_id=market_id,
            city=city,
            target_date=target_date,
            source=self._normalize_actual_source(source),
            metric=self._normalize_metric(metric),
            unit=self._normalize_unit(unit),
            actual_value=actual_value,
            raw_payload=raw_payload or {},
            metadata=metadata or {},
        )
        self.repository.save_weather_actual_record(record)
        return record

    def resolve_from_weather_actual(
        self,
        *,
        market_id: str,
        weather_actual_id: str,
        threshold: float | None = None,
        direction: str | OutcomeDirection | None = None,
        notes: str | None = None,
        metadata: dict | None = None,
    ) -> OutcomeResolutionRecord:
        actual = self.repository.get_weather_actual_record_by_id(weather_actual_id)
        if not actual:
            raise ValueError("weather actual record not found")
        if str(actual.get("market_id")) != str(market_id):
            raise ValueError("weather actual record does not belong to market_id")

        latest_view = self.repository.get_latest_weather_view(market_id)
        resolved_threshold = threshold
        resolved_direction = self._normalize_direction(direction or OutcomeDirection.UNKNOWN)
        weather_view_id = None
        if latest_view:
            weather_view_id = latest_view.get("weather_view_id")
            if resolved_threshold is None:
                resolved_threshold = latest_view.get("threshold")
            if resolved_direction == OutcomeDirection.UNKNOWN and latest_view.get("direction"):
                resolved_direction = self._normalize_direction(str(latest_view["direction"]))

        actual_value = actual.get("actual_value")
        resolved_outcome = ResolvedOutcome.INSUFFICIENT_EVIDENCE
        resolution_status = ResolutionStatus.INSUFFICIENT_EVIDENCE

        if actual_value is not None and resolved_threshold is not None:
            if resolved_direction == OutcomeDirection.ABOVE:
                resolved_outcome = (
                    ResolvedOutcome.YES if float(actual_value) > float(resolved_threshold) else ResolvedOutcome.NO
                )
                resolution_status = ResolutionStatus.RESOLVED
            elif resolved_direction == OutcomeDirection.BELOW:
                resolved_outcome = (
                    ResolvedOutcome.YES if float(actual_value) < float(resolved_threshold) else ResolvedOutcome.NO
                )
                resolution_status = ResolutionStatus.RESOLVED

        record = OutcomeResolutionRecord(
            outcome_resolution_id=f"orr_{uuid4().hex[:12]}",
            market_id=market_id,
            weather_actual_id=weather_actual_id,
            weather_view_id=weather_view_id,
            threshold=resolved_threshold,
            direction=resolved_direction,
            actual_value=actual_value,
            resolved_outcome=resolved_outcome,
            resolution_status=resolution_status,
            resolution_source=MarketOutcomeSource.WEATHER_ACTUAL,
            notes=notes,
            raw_payload={"weather_actual": actual, "weather_view": latest_view or {}},
            metadata=metadata or {},
        )
        self.repository.save_outcome_resolution_record(record)
        return record

    def list_market_outcomes(self, limit: int = 100, market_id: str | None = None) -> list[dict]:
        return self.repository.list_market_outcome_records(limit=limit, market_id=market_id)

    def list_weather_actuals(self, limit: int = 100, market_id: str | None = None) -> list[dict]:
        return self.repository.list_weather_actual_records(limit=limit, market_id=market_id)

    def list_resolutions(
        self,
        limit: int = 100,
        market_id: str | None = None,
        resolution_status: str | ResolutionStatus | None = None,
    ) -> list[dict]:
        return self.repository.list_outcome_resolution_records(
            limit=limit,
            market_id=market_id,
            resolution_status=resolution_status,
        )

    def get_market_bundle(self, market_id: str, limit: int = 100) -> OutcomeBundle:
        return self.repository.get_outcome_bundle(market_id, limit=limit)

    def get_summary(self) -> OutcomeArchiveSummary:
        return self.repository.get_outcome_archive_summary()

    def _normalize_market_source(self, value: str | MarketOutcomeSource) -> MarketOutcomeSource:
        if isinstance(value, MarketOutcomeSource):
            return value
        return MarketOutcomeSource(str(value))

    def _normalize_resolved_outcome(self, value: str | ResolvedOutcome) -> ResolvedOutcome:
        if isinstance(value, ResolvedOutcome):
            return value
        return ResolvedOutcome(str(value))

    def _normalize_resolution_status(self, value: str | ResolutionStatus) -> ResolutionStatus:
        if isinstance(value, ResolutionStatus):
            return value
        return ResolutionStatus(str(value))

    def _normalize_actual_source(self, value: str | WeatherActualSource) -> WeatherActualSource:
        if isinstance(value, WeatherActualSource):
            return value
        return WeatherActualSource(str(value))

    def _normalize_metric(self, value: str | OutcomeMetric) -> OutcomeMetric:
        if isinstance(value, OutcomeMetric):
            return value
        return OutcomeMetric(str(value))

    def _normalize_unit(self, value: str | OutcomeUnit) -> OutcomeUnit:
        if isinstance(value, OutcomeUnit):
            return value
        return OutcomeUnit(str(value))

    def _normalize_direction(self, value: str | OutcomeDirection | None) -> OutcomeDirection:
        if value is None:
            return OutcomeDirection.UNKNOWN
        if isinstance(value, OutcomeDirection):
            return value
        return OutcomeDirection(str(value))
