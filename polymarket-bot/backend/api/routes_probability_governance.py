from __future__ import annotations

from fastapi import APIRouter

from backend.models.weather import ParseConfidence
from backend.models.weather import WeatherDirection
from backend.models.weather import WeatherUnit
from backend.models.weather import WeatherView
from backend.probability.calibration_service import CalibrationService
from backend.probability.market_outcome_service import MarketOutcomeService
from backend.probability.model_promotion_gate import ModelPromotionGate
from backend.probability.probability_comparison_builder import ProbabilityComparisonBuilder
from backend.probability.probability_engine_registry import ProbabilityEngineRegistry
from backend.probability.probability_engine_runner import ProbabilityEngineRunner


def _weather_view_from_row(row: dict) -> WeatherView:
    return WeatherView(
        weather_view_id=row["weather_view_id"],
        evidence_pack_id=row["evidence_pack_id"],
        market_id=row["market_id"],
        city=row["city"],
        target_date=row["target_date"],
        expected_value=row["expected_value"],
        expected_range_low=row["expected_range_low"],
        expected_range_high=row["expected_range_high"],
        sigma=row["sigma"],
        threshold=row["threshold"],
        direction=WeatherDirection(row["direction"]),
        unit=WeatherUnit(row["unit"]),
        confidence=ParseConfidence(row["confidence"]),
        evidence_summary=row.get("evidence_summary", []),
        invalidation_rules=row.get("invalidation_rules", []),
        confirmation_rules=row.get("confirmation_rules", []),
    )


def create_probability_governance_router(repository):
    router = APIRouter(prefix="/api/probability", tags=["probability-governance"])
    registry = ProbabilityEngineRegistry(repository)
    comparison_builder = ProbabilityComparisonBuilder()
    outcome_service = MarketOutcomeService(repository)
    calibration_service = CalibrationService(repository)
    promotion_gate = ModelPromotionGate(repository)

    @router.get("/engines")
    def list_engines():
        return {
            "status": "ok",
            "engines": registry.list_configs(),
            "primary": registry.get_primary_engine_config(),
            "shadow": registry.get_shadow_engine_configs(),
        }

    @router.post("/compare/{market_id}")
    def compare_market_probability(market_id: str):
        weather_view_row = repository.get_latest_weather_view(market_id)
        if not weather_view_row:
            return {
                "status": "error",
                "message": "latest weather view not found",
                "market_id": market_id,
            }
        weather_view = _weather_view_from_row(weather_view_row)
        runner = ProbabilityEngineRunner(
            repository=repository,
            registry=registry,
        )
        runs = runner.run_all(weather_view)
        comparison = comparison_builder.build(runs)
        repository.save_probability_comparison(comparison)
        return {
            "status": "ok",
            "comparison": comparison.model_dump(mode="json"),
        }

    @router.get("/comparison/{market_id}")
    def get_latest_comparison(market_id: str):
        comparison = repository.get_latest_probability_comparison(market_id)
        if not comparison:
            return {
                "status": "error",
                "message": "probability comparison not found",
                "market_id": market_id,
            }
        return {
            "status": "ok",
            "comparison": comparison,
        }

    @router.post("/outcomes")
    def record_market_outcome(payload: dict):
        market_id = payload.get("market_id")
        status = payload.get("status", "PENDING")
        if not market_id:
            return {
                "status": "error",
                "message": "market_id is required",
            }
        try:
            outcome = outcome_service.record_outcome(
                market_id=market_id,
                status=status,
                resolved_direction_hit=payload.get("resolved_direction_hit"),
                resolved_value=payload.get("resolved_value"),
                official_source=payload.get("official_source"),
                notes=payload.get("notes"),
            )
            return {
                "status": "ok",
                "outcome": outcome.model_dump(mode="json"),
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": str(exc),
            }

    @router.get("/outcomes/{market_id}")
    def get_latest_outcome(market_id: str):
        outcome = outcome_service.get_latest_outcome(market_id)
        if not outcome:
            return {
                "status": "error",
                "message": "market outcome not found",
                "market_id": market_id,
            }
        return {
            "status": "ok",
            "outcome": outcome,
        }

    @router.post("/calibrate/{market_id}")
    def calibrate_market(market_id: str):
        try:
            results = calibration_service.calibrate_market(market_id)
            return {
                "status": "ok",
                "results": [r.model_dump(mode="json") for r in results],
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": str(exc),
            }

    @router.get("/calibration/{engine_id}")
    def get_calibration_for_engine(engine_id: str, limit: int = 100):
        return {
            "status": "ok",
            "engine_id": engine_id,
            "results": repository.list_calibration_results_for_engine(engine_id, limit),
        }

    @router.get("/calibration/market/{market_id}")
    def get_calibration_for_market(market_id: str, limit: int = 100):
        return {
            "status": "ok",
            "market_id": market_id,
            "results": repository.list_calibration_results_for_market(market_id, limit),
        }

    @router.post("/promotion/{engine_id}")
    def evaluate_promotion(engine_id: str):
        try:
            decision = promotion_gate.evaluate(engine_id)
            return {
                "status": "ok",
                "decision": decision.model_dump(mode="json"),
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": str(exc),
            }

    @router.get("/promotion/{engine_id}")
    def get_latest_promotion(engine_id: str):
        decision = repository.get_latest_engine_promotion_decision(engine_id)
        if not decision:
            return {
                "status": "error",
                "message": "promotion decision not found",
                "engine_id": engine_id,
            }
        return {
            "status": "ok",
            "decision": decision,
        }

    return router
