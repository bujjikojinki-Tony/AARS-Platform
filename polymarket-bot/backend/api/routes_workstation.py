from __future__ import annotations

from fastapi import APIRouter


def create_workstation_router(repository) -> APIRouter:
    router = APIRouter(prefix="/api/workstation", tags=["workstation"])

    @router.get("/{market_id}")
    def get_workstation(market_id: str):
        candidate = repository.get_latest_candidate_for_market(market_id)
        descriptor = repository.get_latest_weather_descriptor(market_id)
        evidence_pack = repository.get_latest_evidence_pack(market_id)
        sources = repository.list_weather_sources_for_market(market_id)
        weather_view = repository.get_latest_weather_view(market_id)
        probability_view = repository.get_latest_probability_view(market_id)
        probability_comparison = repository.get_latest_probability_comparison(market_id)
        market_outcome = repository.get_latest_market_outcome(market_id)
        if not any([
            candidate,
            descriptor,
            evidence_pack,
            weather_view,
            probability_view,
            probability_comparison,
        ]):
            return {
                "status": "error",
                "message": "no workstation data found for market",
                "market_id": market_id,
            }
        return {
            "status": "ok",
            "market_id": market_id,
            "candidate": candidate,
            "descriptor": descriptor,
            "evidence_pack": evidence_pack,
            "sources": sources,
            "weather_view": weather_view,
            "probability_view": probability_view,
            "probability_comparison": probability_comparison,
            "market_outcome": market_outcome,
        }

    return router
