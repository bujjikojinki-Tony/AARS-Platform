from __future__ import annotations

from fastapi import APIRouter

from backend.emos_shadow.emos_shadow_service import EmosShadowService


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


def create_emos_shadow_router(repository) -> APIRouter:
    router = APIRouter(prefix="/api/emos-shadow", tags=["emos-shadow"])
    service = EmosShadowService(repository)

    @router.get("/summary")
    def get_emos_shadow_summary():
        return {
            "status": "ok",
            "summary": service.get_summary().model_dump(mode="json"),
        }

    @router.get("/runs")
    def list_emos_shadow_runs(
        limit: int = 100,
        market_id: str | None = None,
        run_status: str | None = None,
    ):
        return {
            "status": "ok",
            "items": service.list_runs(limit=limit, market_id=market_id, run_status=run_status),
        }

    @router.get("/diagnostics")
    def list_emos_shadow_diagnostics(
        limit: int = 100,
        market_id: str | None = None,
        emos_shadow_run_id: str | None = None,
    ):
        return {
            "status": "ok",
            "items": service.list_diagnostics(
                limit=limit,
                market_id=market_id,
                emos_shadow_run_id=emos_shadow_run_id,
            ),
        }

    @router.get("/market/{market_id}")
    def get_emos_shadow_market_bundle(market_id: str, limit: int = 100):
        return {
            "status": "ok",
            "market_id": market_id,
            "bundle": service.get_market_bundle(market_id, limit=limit).model_dump(mode="json"),
        }

    @router.post("/build")
    def build_emos_shadow(payload: dict):
        market_id = payload.get("market_id")
        if not market_id:
            return {"status": "error", "message": "market_id is required", "safety": _safety_flags()}
        try:
            result = service.build_for_market(str(market_id))
            return {
                "status": "ok",
                "run": result["run"].model_dump(mode="json"),
                "diagnostic": result["diagnostic"].model_dump(mode="json"),
                "safety": _safety_flags(),
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc), "safety": _safety_flags()}

    @router.post("/build-all")
    def build_all_emos_shadow():
        try:
            results = service.build_all_eligible()
            return {
                "status": "ok",
                "built_count": len(results),
                "runs": [item["run"].model_dump(mode="json") for item in results],
                "diagnostics": [item["diagnostic"].model_dump(mode="json") for item in results],
                "safety": _safety_flags(),
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc), "safety": _safety_flags()}

    return router
