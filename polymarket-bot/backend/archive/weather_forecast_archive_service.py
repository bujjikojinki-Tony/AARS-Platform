from __future__ import annotations

from uuid import uuid4

from backend.models.weather import EvidencePack
from backend.models.weather import WeatherMetric
from backend.models.weather import WeatherSourceRecord
from backend.models.weather import WeatherUnit
from backend.models.weather import WeatherView
from backend.models.weather_archive import WeatherArchiveBundle
from backend.models.weather_archive import WeatherArchiveMetric
from backend.models.weather_archive import WeatherArchiveReason
from backend.models.weather_archive import WeatherArchiveSummary
from backend.models.weather_archive import WeatherArchiveUnit
from backend.models.weather_archive import WeatherEvidenceArchiveRecord
from backend.models.weather_archive import WeatherForecastArchiveRecord
from backend.models.weather_archive import WeatherForecastSourceType
from backend.models.weather_archive import WeatherViewArchiveRecord


class WeatherForecastArchiveService:
    """Passive archive service for weather-side records only."""

    def __init__(self, repository):
        self.repository = repository

    def archive_weather_view(
        self,
        weather_view: WeatherView,
        archive_reason: str | WeatherArchiveReason,
        metadata: dict | None = None,
    ) -> WeatherViewArchiveRecord:
        record = WeatherViewArchiveRecord(
            weather_view_archive_id=f"wva_{uuid4().hex[:12]}",
            market_id=weather_view.market_id,
            weather_view_id=weather_view.weather_view_id,
            evidence_pack_id=weather_view.evidence_pack_id,
            city=weather_view.city,
            target_date=weather_view.target_date,
            expected_value=weather_view.expected_value,
            expected_range_low=weather_view.expected_range_low,
            expected_range_high=weather_view.expected_range_high,
            sigma=weather_view.sigma,
            threshold=weather_view.threshold,
            direction=weather_view.direction.value if hasattr(weather_view.direction, "value") else str(weather_view.direction),
            unit=weather_view.unit.value if hasattr(weather_view.unit, "value") else str(weather_view.unit),
            confidence=weather_view.confidence.value if hasattr(weather_view.confidence, "value") else str(weather_view.confidence),
            raw_payload=weather_view.model_dump(mode="json"),
            metadata=metadata or {},
            archive_reason=self._normalize_reason(archive_reason),
        )
        self.repository.save_weather_view_archive_record(record)
        return record

    def archive_evidence_pack(
        self,
        market_id: str,
        evidence_pack: EvidencePack | dict,
        archive_reason: str | WeatherArchiveReason,
        metadata: dict | None = None,
    ) -> WeatherEvidenceArchiveRecord:
        pack = evidence_pack if isinstance(evidence_pack, EvidencePack) else EvidencePack(**evidence_pack)
        record = WeatherEvidenceArchiveRecord(
            evidence_archive_id=f"wea_{uuid4().hex[:12]}",
            market_id=market_id,
            evidence_pack_id=pack.evidence_pack_id,
            source_ids=[source.source_id for source in pack.sources],
            archived_at=pack.created_at,
            raw_payload=pack.model_dump(mode="json"),
            metadata=metadata or {},
            archive_reason=self._normalize_reason(archive_reason),
        )
        self.repository.save_weather_evidence_archive_record(record)
        return record

    def archive_forecast_record(
        self,
        market_id: str,
        weather_view_id: str | None,
        evidence_pack_id: str | None,
        source_id: str,
        source_type: str | WeatherForecastSourceType,
        metric: str | WeatherArchiveMetric,
        unit: str | WeatherArchiveUnit,
        expected_value: float | None,
        expected_range_low: float | None,
        expected_range_high: float | None,
        sigma: float | None,
        archive_reason: str | WeatherArchiveReason,
        *,
        city: str | None = None,
        target_date: str | None = None,
        fetched_at: str | None = None,
        raw_payload: dict | None = None,
        metadata: dict | None = None,
    ) -> WeatherForecastArchiveRecord:
        record = WeatherForecastArchiveRecord(
            forecast_archive_id=f"wfa_{uuid4().hex[:12]}",
            market_id=market_id,
            weather_view_id=weather_view_id,
            evidence_pack_id=evidence_pack_id,
            city=city,
            target_date=target_date,
            source_id=source_id,
            source_type=self._normalize_source_type(source_type),
            metric=self._normalize_metric(metric),
            unit=self._normalize_unit(unit),
            expected_value=expected_value,
            expected_range_low=expected_range_low,
            expected_range_high=expected_range_high,
            sigma=sigma,
            fetched_at=fetched_at,
            raw_payload=raw_payload or {},
            metadata=metadata or {},
            archive_reason=self._normalize_reason(archive_reason),
        )
        self.repository.save_weather_forecast_archive_record(record)
        return record

    def archive_probability_build_bundle(
        self,
        *,
        weather_view: WeatherView,
        evidence_pack: EvidencePack,
        source_records: list[WeatherSourceRecord],
        archive_reason: str | WeatherArchiveReason = WeatherArchiveReason.PROBABILITY_BUILD_CAPTURE,
        metadata: dict | None = None,
    ) -> dict[str, object]:
        weather_view_record = self.archive_weather_view(weather_view, archive_reason, metadata=metadata)
        evidence_record = self.archive_evidence_pack(
            weather_view.market_id,
            evidence_pack,
            archive_reason,
            metadata=metadata,
        )
        forecast_records = [
            self.archive_forecast_record(
                market_id=weather_view.market_id,
                weather_view_id=weather_view.weather_view_id,
                evidence_pack_id=evidence_pack.evidence_pack_id,
                source_id=source.source_id,
                source_type=self._infer_source_type(source),
                metric=self._infer_metric(evidence_pack),
                unit=self._infer_unit(source.unit),
                expected_value=source.normalized_value,
                expected_range_low=weather_view.expected_range_low,
                expected_range_high=weather_view.expected_range_high,
                sigma=weather_view.sigma,
                city=source.city,
                target_date=source.target_date,
                fetched_at=source.fetched_at,
                raw_payload=source.raw_payload,
                metadata=metadata,
                archive_reason=archive_reason,
            )
            for source in source_records
        ]
        return {
            "weather_view": weather_view_record,
            "evidence": evidence_record,
            "forecasts": forecast_records,
        }

    def archive_existing_latest_market_bundle(
        self,
        market_id: str,
        archive_reason: str | WeatherArchiveReason = WeatherArchiveReason.MANUAL_CAPTURE,
        metadata: dict | None = None,
    ) -> dict[str, object]:
        latest_view = self.repository.get_latest_weather_view(market_id)
        if not latest_view:
            return {
                "weather_views": [],
                "evidence": [],
                "forecasts": [],
                "warnings": ["latest weather view not found"],
            }
        weather_view = WeatherView(**self._coerce_weather_view_payload(latest_view))
        evidence_payload = self.repository.get_latest_evidence_pack(market_id)
        evidence_pack = EvidencePack(**self._coerce_evidence_pack_payload(evidence_payload)) if evidence_payload else None
        sources = [
            WeatherSourceRecord(**self._coerce_source_payload(item))
            for item in self.repository.list_weather_sources_for_market(market_id, limit=100)
        ]
        result: dict[str, object] = {"warnings": []}
        result["weather_views"] = [self.archive_weather_view(weather_view, archive_reason, metadata=metadata)]
        if evidence_pack is not None:
            result["evidence"] = [
                self.archive_evidence_pack(
                    market_id,
                    evidence_pack,
                    archive_reason,
                    metadata=metadata,
                )
            ]
            result["forecasts"] = [
                self.archive_forecast_record(
                    market_id=market_id,
                    weather_view_id=weather_view.weather_view_id,
                    evidence_pack_id=evidence_pack.evidence_pack_id,
                    source_id=source.source_id,
                    source_type=self._infer_source_type(source),
                    metric=self._infer_metric(evidence_pack),
                    unit=self._infer_unit(source.unit),
                    expected_value=source.normalized_value,
                    expected_range_low=weather_view.expected_range_low,
                    expected_range_high=weather_view.expected_range_high,
                    sigma=weather_view.sigma,
                    city=source.city,
                    target_date=source.target_date,
                    fetched_at=source.fetched_at,
                    raw_payload=source.raw_payload,
                    metadata=metadata,
                    archive_reason=archive_reason,
                )
                for source in sources
            ]
        else:
            result["evidence"] = []
            result["forecasts"] = []
            result["warnings"] = ["latest evidence pack not found"]
        return result

    def list_recent_weather_views(
        self,
        limit: int = 100,
        archive_reason: str | WeatherArchiveReason | None = None,
    ) -> list[dict]:
        return self.repository.list_weather_view_archive(limit=limit, archive_reason=archive_reason)

    def list_recent_forecasts(
        self,
        limit: int = 100,
        source_type: str | WeatherForecastSourceType | None = None,
        archive_reason: str | WeatherArchiveReason | None = None,
    ) -> list[dict]:
        return self.repository.list_weather_forecast_archive(
            limit=limit,
            source_type=source_type,
            archive_reason=archive_reason,
        )

    def list_recent_evidence(
        self,
        limit: int = 100,
        archive_reason: str | WeatherArchiveReason | None = None,
    ) -> list[dict]:
        return self.repository.list_weather_evidence_archive(limit=limit, archive_reason=archive_reason)

    def get_market_bundle(self, market_id: str, limit: int = 100) -> WeatherArchiveBundle:
        return self.repository.get_weather_archive_bundle(market_id, limit=limit)

    def get_summary(self) -> WeatherArchiveSummary:
        return self.repository.get_weather_archive_summary()

    def _normalize_reason(self, value: str | WeatherArchiveReason) -> WeatherArchiveReason:
        if isinstance(value, WeatherArchiveReason):
            return value
        return WeatherArchiveReason(str(value))

    def _normalize_source_type(self, value: str | WeatherForecastSourceType) -> WeatherForecastSourceType:
        if isinstance(value, WeatherForecastSourceType):
            return value
        return WeatherForecastSourceType(str(value))

    def _normalize_metric(self, value: str | WeatherArchiveMetric) -> WeatherArchiveMetric:
        if isinstance(value, WeatherArchiveMetric):
            return value
        return WeatherArchiveMetric(str(value))

    def _normalize_unit(self, value: str | WeatherArchiveUnit) -> WeatherArchiveUnit:
        if isinstance(value, WeatherArchiveUnit):
            return value
        return WeatherArchiveUnit(str(value))

    def _infer_source_type(self, source: WeatherSourceRecord) -> WeatherForecastSourceType:
        name = f"{source.source_name} {source.source_id}".lower()
        if "openmeteo" in name or "open_meteo" in name or "open-meteo" in name:
            return WeatherForecastSourceType.OPEN_METEO
        if "noaa" in name:
            return WeatherForecastSourceType.NOAA_PLACEHOLDER
        if "mock" in name or "placeholder" in name:
            return WeatherForecastSourceType.MOCK
        return WeatherForecastSourceType.UNKNOWN

    def _infer_metric(self, evidence_pack: EvidencePack) -> WeatherArchiveMetric:
        metric = evidence_pack.descriptor.metric
        if metric == WeatherMetric.DAILY_HIGH:
            return WeatherArchiveMetric.TEMPERATURE_HIGH
        if metric == WeatherMetric.DAILY_LOW:
            return WeatherArchiveMetric.TEMPERATURE_LOW
        if metric == WeatherMetric.PRECIPITATION:
            return WeatherArchiveMetric.RAINFALL
        return WeatherArchiveMetric.UNKNOWN

    def _infer_unit(self, unit: WeatherUnit) -> WeatherArchiveUnit:
        if unit == WeatherUnit.C:
            return WeatherArchiveUnit.C
        if unit == WeatherUnit.F:
            return WeatherArchiveUnit.F
        if unit == WeatherUnit.MM:
            return WeatherArchiveUnit.MM
        if unit == WeatherUnit.IN:
            return WeatherArchiveUnit.INCH
        return WeatherArchiveUnit.UNKNOWN

    def _coerce_weather_view_payload(self, item: dict) -> dict:
        payload = dict(item)
        payload.pop("id", None)
        return payload

    def _coerce_source_payload(self, item: dict) -> dict:
        payload = dict(item)
        payload.pop("id", None)
        return payload

    def _coerce_evidence_pack_payload(self, item: dict | None) -> dict:
        if not item:
            return {}
        payload = dict(item)
        payload.pop("id", None)
        return payload
