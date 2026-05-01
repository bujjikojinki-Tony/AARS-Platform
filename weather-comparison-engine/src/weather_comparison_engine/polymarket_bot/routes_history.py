from __future__ import annotations


class HistoryRoutes:
    def __init__(self, repositories) -> None:
        self.repositories = repositories

    def get_signals(self) -> dict:
        rows = self.repositories.strategy_signals.list_all()
        return {"ok": True, "count": len(rows), "items": [row.to_record() for row in rows]}

    def get_candidates(self) -> dict:
        rows = self.repositories.opportunity_candidates.list_all()
        return {"ok": True, "count": len(rows), "items": [row.to_record() for row in rows]}

    def get_simulations(self) -> dict:
        rows = self.repositories.simulation_results.list_all()
        return {"ok": True, "count": len(rows), "items": [row.to_record() for row in rows]}

    def get_audit(self) -> dict:
        rows = self.repositories.audit_logs.list_all()
        return {"ok": True, "count": len(rows), "items": [row.to_record() for row in rows]}
