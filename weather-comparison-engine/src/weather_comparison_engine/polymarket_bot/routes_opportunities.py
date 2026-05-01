from __future__ import annotations


class OpportunityRoutes:
    def __init__(self, repositories, strategy_runner) -> None:
        self.repositories = repositories
        self.strategy_runner = strategy_runner

    def post_scan(self) -> dict:
        candidates = self.strategy_runner.run_once()
        return {
            "ok": True,
            "candidate_count": len(candidates),
            "candidates": [candidate.to_record() for candidate in candidates],
        }

    def get_opportunities(self) -> dict:
        candidates = self.repositories.opportunity_candidates.list_all()
        return {
            "ok": True,
            "count": len(candidates),
            "items": [candidate.to_record() for candidate in candidates],
        }
