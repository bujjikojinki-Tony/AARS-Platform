from __future__ import annotations

from fastapi import APIRouter

from backend.command_review.command_review_service import CommandReviewService


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


def create_command_review_router(repository) -> APIRouter:
    router = APIRouter(prefix="/api/command-review", tags=["command-review"])
    service = CommandReviewService(repository)

    @router.get("/summary")
    def get_command_review_summary():
        return {
            "status": "ok",
            "summary": service.get_summary().model_dump(mode="json"),
        }

    @router.get("/reviews")
    def list_command_reviews(
        limit: int = 100,
        market_id: str | None = None,
        review_status: str | None = None,
        approval_status: str | None = None,
        gate_status: str | None = None,
    ):
        return {
            "status": "ok",
            "items": service.list_reviews(
                limit=limit,
                market_id=market_id,
                review_status=review_status,
                approval_status=approval_status,
                gate_status=gate_status,
            ),
        }

    @router.get("/market/{market_id}")
    def get_command_review_market_bundle(market_id: str, limit: int = 100):
        return {
            "status": "ok",
            "market_id": market_id,
            "bundle": service.get_market_bundle(market_id, limit=limit).model_dump(mode="json"),
        }

    @router.post("/build")
    def build_command_review(payload: dict):
        market_id = payload.get("market_id")
        if not market_id:
            return {"status": "error", "message": "market_id is required", "safety": _safety_flags()}
        try:
            record = service.build_for_market(
                str(market_id),
                command_name=str(payload.get("command_name") or "/review"),
                source_page=str(payload.get("source_page") or "command"),
                target_page=str(payload.get("target_page") or "history"),
                command_path=str(payload.get("command_path") or "/api/command-review/build"),
                approval_status=payload.get("approval_status"),
                review_status=payload.get("review_status"),
                recommendation=payload.get("recommendation"),
                metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else None,
                raw_payload=payload.get("raw_payload") if isinstance(payload.get("raw_payload"), dict) else None,
            )
            return {
                "status": "ok",
                "record": record.model_dump(mode="json"),
                "safety": _safety_flags(),
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc), "safety": _safety_flags()}

    @router.post("/build-all")
    def build_all_command_reviews():
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
