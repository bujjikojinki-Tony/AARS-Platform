from __future__ import annotations

from fastapi import APIRouter

from backend.calibration_memory.backtest_memory_builder import BacktestMemoryBuilder
from backend.calibration_memory.calibration_sample_builder import CalibrationSampleBuilder


def _safety_flags(*, candidates_created: bool = False) -> dict[str, bool]:
    return {
        "probability_engine_called": False,
        "strategy_runner_called": False,
        "candidates_created": candidates_created,
        "simulation_triggered": False,
        "execution_triggered": False,
        "promotion_triggered": False,
        "active_engine_changed": False,
    }


def create_calibration_memory_router(repository) -> APIRouter:
    router = APIRouter(prefix="/api/calibration-memory", tags=["calibration-memory"])
    sample_builder = CalibrationSampleBuilder(repository)
    backtest_builder = BacktestMemoryBuilder(repository)

    @router.get("/summary")
    def get_summary():
        return {
            "status": "ok",
            "summary": repository.get_calibration_memory_summary().model_dump(mode="json"),
        }

    @router.get("/samples")
    def list_samples(
        limit: int = 100,
        market_id: str | None = None,
        engine_id: str | None = None,
        sample_status: str | None = None,
        sample_eligibility: str | None = None,
    ):
        return {
            "status": "ok",
            "items": repository.list_calibration_samples(
                limit=limit,
                market_id=market_id,
                engine_id=engine_id,
                sample_status=sample_status,
                sample_eligibility=sample_eligibility,
            ),
        }

    @router.get("/backtests")
    def list_backtests(
        limit: int = 100,
        market_id: str | None = None,
        engine_id: str | None = None,
        backtest_status: str | None = None,
        sample_eligibility: str | None = None,
        hypothetical_action: str | None = None,
    ):
        return {
            "status": "ok",
            "items": repository.list_backtest_memory_records(
                limit=limit,
                market_id=market_id,
                engine_id=engine_id,
                backtest_status=backtest_status,
                sample_eligibility=sample_eligibility,
                hypothetical_action=hypothetical_action,
            ),
        }

    @router.get("/market/{market_id}")
    def get_market_bundle(market_id: str, limit: int = 100):
        bundle = repository.get_calibration_memory_bundle(market_id, limit=limit)
        return {
            "status": "ok",
            "market_id": market_id,
            "bundle": bundle.model_dump(mode="json"),
        }

    @router.get("/eligibility/{market_id}")
    def get_eligibility(market_id: str):
        return {
            "status": "ok",
            "market_id": market_id,
            "eligibility": sample_builder.check_eligibility(market_id),
            "safety": _safety_flags(),
        }

    @router.post("/build-sample")
    def build_sample(payload: dict):
        market_id = payload.get("market_id")
        if not market_id:
            return {"status": "error", "message": "market_id is required", "safety": _safety_flags()}
        before = len(repository.list_table("opportunity_candidates", limit=1000))
        try:
            sample = sample_builder.build_for_market(str(market_id))
            after = len(repository.list_table("opportunity_candidates", limit=1000))
            return {
                "status": "ok",
                "sample": sample.model_dump(mode="json"),
                "eligibility": sample_builder.check_eligibility(str(market_id)),
                "safety": _safety_flags(candidates_created=before != after),
            }
        except Exception as exc:
            after = len(repository.list_table("opportunity_candidates", limit=1000))
            return {
                "status": "error",
                "message": str(exc),
                "eligibility": sample_builder.check_eligibility(str(market_id)),
                "safety": _safety_flags(candidates_created=before != after),
            }

    @router.post("/build-backtest")
    def build_backtest(payload: dict):
        calibration_sample_id = payload.get("calibration_sample_id")
        market_id = payload.get("market_id")
        if not calibration_sample_id and not market_id:
            return {
                "status": "error",
                "message": "calibration_sample_id or market_id is required",
                "safety": _safety_flags(),
            }
        sample = None
        if calibration_sample_id:
            sample = repository.get_calibration_sample_by_id(str(calibration_sample_id))
        elif market_id:
            rows = repository.list_calibration_samples(market_id=str(market_id), limit=1)
            sample = rows[0] if rows else None
        if not sample:
            return {
                "status": "error",
                "message": "calibration sample not found",
                "safety": _safety_flags(),
            }
        before = len(repository.list_table("opportunity_candidates", limit=1000))
        try:
            record = backtest_builder.build_from_sample(
                sample,
                edge_threshold=payload.get("edge_threshold"),
            )
            after = len(repository.list_table("opportunity_candidates", limit=1000))
            return {
                "status": "ok",
                "backtest": record.model_dump(mode="json"),
                "safety": _safety_flags(candidates_created=before != after),
            }
        except Exception as exc:
            after = len(repository.list_table("opportunity_candidates", limit=1000))
            return {
                "status": "error",
                "message": str(exc),
                "safety": _safety_flags(candidates_created=before != after),
            }

    @router.post("/build-all-eligible")
    def build_all_eligible():
        before = len(repository.list_table("opportunity_candidates", limit=1000))
        try:
            items = sample_builder.build_all_eligible()
            after = len(repository.list_table("opportunity_candidates", limit=1000))
            return {
                "status": "ok",
                "built_count": len(items),
                "samples": [item.model_dump(mode="json") for item in items],
                "safety": _safety_flags(candidates_created=before != after),
            }
        except Exception as exc:
            after = len(repository.list_table("opportunity_candidates", limit=1000))
            return {
                "status": "error",
                "message": str(exc),
                "safety": _safety_flags(candidates_created=before != after),
            }

    return router
