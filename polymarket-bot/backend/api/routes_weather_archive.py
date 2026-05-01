from __future__ import annotations

from fastapi import APIRouter

from backend.archive.weather_forecast_archive_service import WeatherForecastArchiveService
from backend.models.weather import WeatherView
from backend.models.weather_archive import WeatherArchiveMetric
from backend.models.weather_archive import WeatherArchiveReason
from backend.models.weather_archive import WeatherArchiveUnit
from backend.models.weather_archive import WeatherForecastSourceType


def create_weather_archive_router(services) -> APIRouter:
    router = APIRouter(prefix="/api/weather-archive", tags=["weather-archive"])
    archive_service = WeatherForecastArchiveService(services.repository)

    @router.get("/summary")
    def get_weather_archive_summary():
        return {"status": "ok", "summary": archive_service.get_summary().model_dump(mode="json")}

    @router.get("/views")
    def list_weather_archive_views(limit: int = 100, archive_reason: str | None = None):
        return {
            "status": "ok",
            "items": archive_service.list_recent_weather_views(limit=limit, archive_reason=archive_reason),
        }

    @router.get("/forecasts")
    def list_weather_archive_forecasts(
        limit: int = 100,
        source_type: str | None = None,
        archive_reason: str | None = None,
    ):
        return {
            "status": "ok",
            "items": archive_service.list_recent_forecasts(
                limit=limit,
                source_type=source_type,
                archive_reason=archive_reason,
            ),
        }

    @router.get("/evidence")
    def list_weather_archive_evidence(limit: int = 100, archive_reason: str | None = None):
        return {
            "status": "ok",
            "items": archive_service.list_recent_evidence(limit=limit, archive_reason=archive_reason),
        }

    @router.get("/market/{market_id}")
    def get_weather_archive_market_bundle(market_id: str, limit: int = 100):
        bundle = archive_service.get_market_bundle(market_id, limit=limit).model_dump(mode="json")
        return {"status": "ok", "market_id": market_id, **bundle}

    @router.post("/view")
    def post_weather_archive_view(payload: dict):
        required = [
            "market_id",
            "weather_view_id",
            "city",
            "target_date",
            "expected_value",
            "expected_range_low",
            "expected_range_high",
            "sigma",
        ]
        missing = [field for field in required if field not in payload]
        if missing:
            return {"status": "error", "message": f"missing required fields: {', '.join(missing)}"}
        record = archive_service.archive_weather_view(
            WeatherView(**payload),
            archive_reason=payload.get("archive_reason") or WeatherArchiveReason.MANUAL_CAPTURE.value,
            metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else None,
        )
        return {"status": "ok", "record": record.model_dump(mode="json")}

    @router.post("/forecast")
    def post_weather_archive_forecast(payload: dict):
        required = ["market_id", "source_id"]
        missing = [field for field in required if field not in payload]
        if missing:
            return {"status": "error", "message": f"missing required fields: {', '.join(missing)}"}
        record = archive_service.archive_forecast_record(
            market_id=str(payload["market_id"]),
            weather_view_id=payload.get("weather_view_id"),
            evidence_pack_id=payload.get("evidence_pack_id"),
            source_id=str(payload["source_id"]),
            source_type=payload.get("source_type") or WeatherForecastSourceType.UNKNOWN.value,
            metric=payload.get("metric") or WeatherArchiveMetric.UNKNOWN.value,
            unit=payload.get("unit") or WeatherArchiveUnit.UNKNOWN.value,
            expected_value=payload.get("expected_value"),
            expected_range_low=payload.get("expected_range_low"),
            expected_range_high=payload.get("expected_range_high"),
            sigma=payload.get("sigma"),
            city=payload.get("city"),
            target_date=payload.get("target_date"),
            fetched_at=payload.get("fetched_at"),
            raw_payload=payload.get("raw_payload") if isinstance(payload.get("raw_payload"), dict) else None,
            metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else None,
            archive_reason=payload.get("archive_reason") or WeatherArchiveReason.MANUAL_CAPTURE.value,
        )
        return {"status": "ok", "record": record.model_dump(mode="json")}

    @router.post("/evidence")
    def post_weather_archive_evidence(payload: dict):
        required = ["market_id", "evidence_pack_id"]
        missing = [field for field in required if field not in payload]
        if missing:
            return {"status": "error", "message": f"missing required fields: {', '.join(missing)}"}
        evidence_payload = {
            "evidence_pack_id": payload["evidence_pack_id"],
            "market_id": payload["market_id"],
            "descriptor": payload.get("descriptor") or {},
            "sources": payload.get("sources") or [],
            "evidence_freshness": payload.get("evidence_freshness") or "MISSING",
            "evidence_conflict_level": payload.get("evidence_conflict_level") or "NONE",
            "raw_refs": payload.get("raw_refs") or [],
        }
        record = archive_service.archive_evidence_pack(
            str(payload["market_id"]),
            evidence_payload,
            archive_reason=payload.get("archive_reason") or WeatherArchiveReason.MANUAL_CAPTURE.value,
            metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else None,
        )
        return {"status": "ok", "record": record.model_dump(mode="json")}

    @router.post("/latest/{market_id}")
    def post_weather_archive_latest(market_id: str):
        before_candidates = len(services.repository.list_table("opportunity_candidates", limit=1000))
        result = archive_service.archive_existing_latest_market_bundle(
            market_id,
            archive_reason=WeatherArchiveReason.MANUAL_CAPTURE,
            metadata={"capture_source": "latest_weather_view"},
        )
        after_candidates = len(services.repository.list_table("opportunity_candidates", limit=1000))
        weather_views = result.get("weather_views") or []
        evidence = result.get("evidence") or []
        forecasts = result.get("forecasts") or []
        warnings = list(result.get("warnings") or [])
        return {
            "status": "ok",
            "market_id": market_id,
            "weather_views": [item.model_dump(mode="json") for item in weather_views],
            "evidence": [item.model_dump(mode="json") for item in evidence],
            "forecasts": [item.model_dump(mode="json") for item in forecasts],
            "warnings": warnings,
            "safety": {
                "weather_fetch_triggered": False,
                "strategy_runner_called": False,
                "candidates_created": before_candidates != after_candidates,
                "simulation_triggered": False,
                "execution_triggered": False,
            },
        }

    return router
