from __future__ import annotations

from fastapi import APIRouter

from backend.models.outcome import MarketOutcomeSource
from backend.models.outcome import OutcomeDirection
from backend.models.outcome import OutcomeMetric
from backend.models.outcome import OutcomeUnit
from backend.models.outcome import ResolvedOutcome
from backend.models.outcome import ResolutionStatus
from backend.models.outcome import WeatherActualSource
from backend.outcome.outcome_resolver_read_only_service import OutcomeResolverReadOnlyService


def create_outcomes_router(services) -> APIRouter:
    router = APIRouter(prefix="/api/outcomes", tags=["outcomes"])
    resolver = OutcomeResolverReadOnlyService(services.repository)

    @router.get("/summary")
    def get_outcome_summary():
        return {"status": "ok", "summary": resolver.get_summary().model_dump(mode="json")}

    @router.get("/markets")
    def list_market_outcomes(limit: int = 100, market_id: str | None = None):
        return {
            "status": "ok",
            "items": resolver.list_market_outcomes(limit=limit, market_id=market_id),
        }

    @router.get("/weather-actuals")
    def list_weather_actuals(limit: int = 100, market_id: str | None = None):
        return {
            "status": "ok",
            "items": resolver.list_weather_actuals(limit=limit, market_id=market_id),
        }

    @router.get("/resolutions")
    def list_resolutions(
        limit: int = 100,
        market_id: str | None = None,
        resolution_status: str | None = None,
    ):
        return {
            "status": "ok",
            "items": resolver.list_resolutions(
                limit=limit,
                market_id=market_id,
                resolution_status=resolution_status,
            ),
        }

    @router.get("/market/{market_id}")
    def get_market_bundle(market_id: str, limit: int = 100):
        bundle = resolver.get_market_bundle(market_id, limit=limit)
        return {"status": "ok", "market_id": market_id, "bundle": bundle.model_dump(mode="json")}

    @router.post("/market")
    def post_market_outcome(payload: dict):
        market_id = payload.get("market_id")
        if not market_id:
            return {"status": "error", "message": "market_id is required"}
        try:
            record = resolver.save_market_outcome(
                market_id=str(market_id),
                question=payload.get("question"),
                source=payload.get("source") or MarketOutcomeSource.MANUAL.value,
                resolved_outcome=payload.get("resolved_outcome") or ResolvedOutcome.UNKNOWN.value,
                resolution_status=payload.get("resolution_status") or ResolutionStatus.UNKNOWN.value,
                resolved_value=payload.get("resolved_value"),
                notes=payload.get("notes"),
                raw_payload=payload.get("raw_payload") if isinstance(payload.get("raw_payload"), dict) else None,
                metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else None,
            )
            return {
                "status": "ok",
                "record": record.model_dump(mode="json"),
                "safety": {
                    "strategy_runner_called": False,
                    "simulation_triggered": False,
                    "execution_triggered": False,
                    "calibration_triggered": False,
                    "promotion_triggered": False,
                },
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    @router.post("/weather-actual")
    def post_weather_actual(payload: dict):
        market_id = payload.get("market_id")
        if not market_id:
            return {"status": "error", "message": "market_id is required"}
        try:
            record = resolver.save_weather_actual(
                market_id=str(market_id),
                city=payload.get("city"),
                target_date=payload.get("target_date"),
                source=payload.get("source") or WeatherActualSource.MANUAL.value,
                metric=payload.get("metric") or OutcomeMetric.UNKNOWN.value,
                unit=payload.get("unit") or OutcomeUnit.UNKNOWN.value,
                actual_value=payload.get("actual_value"),
                raw_payload=payload.get("raw_payload") if isinstance(payload.get("raw_payload"), dict) else None,
                metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else None,
            )
            return {
                "status": "ok",
                "record": record.model_dump(mode="json"),
                "safety": {
                    "strategy_runner_called": False,
                    "simulation_triggered": False,
                    "execution_triggered": False,
                    "calibration_triggered": False,
                    "promotion_triggered": False,
                },
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    @router.post("/resolve-from-weather")
    def post_resolve_from_weather(payload: dict):
        market_id = payload.get("market_id")
        weather_actual_id = payload.get("weather_actual_id")
        if not market_id or not weather_actual_id:
            return {"status": "error", "message": "market_id and weather_actual_id are required"}
        try:
            record = resolver.resolve_from_weather_actual(
                market_id=str(market_id),
                weather_actual_id=str(weather_actual_id),
                threshold=payload.get("threshold"),
                direction=payload.get("direction") or OutcomeDirection.UNKNOWN.value,
                notes=payload.get("notes"),
                metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else None,
            )
            return {
                "status": "ok",
                "record": record.model_dump(mode="json"),
                "safety": {
                    "strategy_runner_called": False,
                    "simulation_triggered": False,
                    "execution_triggered": False,
                    "calibration_triggered": False,
                    "promotion_triggered": False,
                },
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    return router
