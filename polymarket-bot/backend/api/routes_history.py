from __future__ import annotations

from fastapi import APIRouter


def create_history_router(repository) -> APIRouter:
    router = APIRouter(prefix="/api/history", tags=["history"])

    @router.get("/signals")
    def history_signals(limit: int = 100):
        return repository.list_table("strategy_signals", limit)

    @router.get("/candidates")
    def history_candidates(limit: int = 100):
        return repository.list_table("opportunity_candidates", limit)

    @router.get("/simulations")
    def history_simulations(limit: int = 100):
        return repository.list_table("simulation_results", limit)

    @router.get("/audit")
    def history_audit(limit: int = 100):
        return repository.list_table("audit_logs", limit)

    return router
