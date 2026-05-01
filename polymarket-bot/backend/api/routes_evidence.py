from __future__ import annotations

from fastapi import APIRouter


def create_evidence_router(repository) -> APIRouter:
    router = APIRouter(prefix="/api/evidence", tags=["evidence"])

    @router.get("/packs")
    def list_evidence_packs(limit: int = 100):
        return {"status": "ok", "items": repository.list_evidence_packs(limit)}

    @router.get("/market/{market_id}")
    def get_market_evidence(market_id: str):
        pack = repository.get_latest_evidence_pack(market_id)
        sources = repository.list_weather_sources_for_market(market_id)
        if not pack:
            return {
                "status": "error",
                "message": "evidence not found",
                "sources": sources,
            }
        return {"status": "ok", "evidence_pack": pack, "sources": sources}

    return router
