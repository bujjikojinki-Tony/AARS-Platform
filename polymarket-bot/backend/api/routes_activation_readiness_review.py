from __future__ import annotations

from fastapi import APIRouter

from backend.activation_readiness_review.activation_readiness_review_service import (
    ActivationReadinessReviewService,
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


def create_activation_readiness_review_router(repository) -> APIRouter:
    router = APIRouter(prefix="/api/activation-readiness-review", tags=["activation-readiness-review"])
    service = ActivationReadinessReviewService(repository)

    @router.get("/summary")
    def get_activation_readiness_review_summary():
        return {
            "status": "ok",
            "summary": service.get_summary().model_dump(mode="json"),
        }

    @router.get("/reviews")
    def list_activation_readiness_reviews(
        limit: int = 100,
        market_id: str | None = None,
        readiness_status: str | None = None,
        recommendation: str | None = None,
        approval_status: str | None = None,
    ):
        return {
            "status": "ok",
            "items": service.list_reviews(
                limit=limit,
                market_id=market_id,
                readiness_status=readiness_status,
                recommendation=recommendation,
                approval_status=approval_status,
            ),
        }

    @router.get("/market/{market_id}")
    def get_activation_readiness_review_market_bundle(market_id: str, limit: int = 100):
        return {
            "status": "ok",
            "market_id": market_id,
            "bundle": service.get_market_bundle(market_id, limit=limit).model_dump(mode="json"),
        }

    @router.post("/build")
    def build_activation_readiness_review(payload: dict):
        market_id = payload.get("market_id")
        if not market_id:
            return {"status": "error", "message": "market_id is required", "safety": _safety_flags()}
        try:
            record = service.build_for_market(
                str(market_id),
                approval_window_review_id=payload.get("approval_window_review_id"),
                raw_payload=payload.get("raw_payload") if isinstance(payload.get("raw_payload"), dict) else None,
                metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else None,
            )
            return {
                "status": "ok",
                "record": record.model_dump(mode="json"),
                "safety": _safety_flags(),
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc), "safety": _safety_flags()}

    @router.post("/build-all")
    def build_all_activation_readiness_reviews():
        try:
            records = service.build_all_eligible()
            return {
                "status": "ok",
                "built_count": len(records),
                "records": [item.model_dump(mode="json") for item in records],
                "safety": _safety_flags(),
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc), "safety": _safety_flags()}

    return router
