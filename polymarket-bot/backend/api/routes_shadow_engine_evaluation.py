from __future__ import annotations

from fastapi import APIRouter

from backend.shadow_engine_evaluation.shadow_engine_evaluation_service import (
    ShadowEngineEvaluationService,
)


def _safety_flags() -> dict[str, bool]:
    return {
        "probability_engine_called": False,
        "strategy_runner_called": False,
        "candidates_created": False,
        "simulation_triggered": False,
        "execution_triggered": False,
        "promotion_triggered": False,
        "active_engine_changed": False,
    }


def create_shadow_engine_evaluation_router(repository) -> APIRouter:
    router = APIRouter(prefix="/api/shadow-evaluation", tags=["shadow-evaluation"])
    service = ShadowEngineEvaluationService(repository)

    @router.get("/summary")
    def get_shadow_evaluation_summary():
        return {
            "status": "ok",
            "summary": service.get_summary().model_dump(mode="json"),
        }

    @router.get("/evaluations")
    def list_shadow_evaluations(
        limit: int = 100,
        market_id: str | None = None,
        evaluation_status: str | None = None,
        best_engine: str | None = None,
    ):
        return {
            "status": "ok",
            "items": service.list_evaluations(
                limit=limit,
                market_id=market_id,
                evaluation_status=evaluation_status,
                best_engine=best_engine,
            ),
        }

    @router.get("/market/{market_id}")
    def get_shadow_evaluation_market_bundle(market_id: str, limit: int = 100):
        return {
            "status": "ok",
            "market_id": market_id,
            "bundle": service.get_market_bundle(market_id, limit=limit).model_dump(mode="json"),
        }

    @router.post("/build")
    def build_shadow_evaluation(payload: dict):
        market_id = payload.get("market_id")
        if not market_id:
            return {"status": "error", "message": "market_id is required", "safety": _safety_flags()}
        try:
            record = service.build_for_market(str(market_id))
            return {
                "status": "ok",
                "evaluation": record.model_dump(mode="json"),
                "safety": _safety_flags(),
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc), "safety": _safety_flags()}

    @router.post("/build-all")
    def build_all_shadow_evaluations():
        try:
            records = service.build_all_eligible()
            return {
                "status": "ok",
                "built_count": len(records),
                "evaluations": [item.model_dump(mode="json") for item in records],
                "safety": _safety_flags(),
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc), "safety": _safety_flags()}

    return router
