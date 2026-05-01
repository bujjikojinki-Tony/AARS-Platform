from __future__ import annotations

from fastapi import APIRouter

from backend.archive.market_snapshot_archive_service import MarketSnapshotArchiveService
from backend.models.core import AuditLogEvent
from backend.models.enums import ActionStatus
from backend.models.polymarket import MarketSourceMode
from backend.models.snapshot_archive import SnapshotArchiveReason


def create_opportunities_router(
    repository,
    strategy_runner,
    market_source_mode: MarketSourceMode | str = MarketSourceMode.MOCK_ONLY,
) -> APIRouter:
    router = APIRouter(prefix="/api/opportunities", tags=["opportunities"])
    archive_service = MarketSnapshotArchiveService(repository)

    @router.post("/scan")
    def scan_opportunities(archive_on_scan: bool = True):
        candidates = strategy_runner.run_once()
        archive_saved_count = 0
        archive_warnings: list[str] = []
        if archive_on_scan:
            try:
                records = archive_service.archive_snapshots(
                    snapshots=list(getattr(strategy_runner, "last_market_snapshots", []) or []),
                    market_source_mode=market_source_mode,
                    archive_reason=SnapshotArchiveReason.SCAN_CAPTURE,
                    metadata={"capture_source": "scan"},
                )
                archive_saved_count = len(records)
            except Exception as exc:
                archive_warnings.append(f"scan archive failed safely: {exc}")
        return {
            "status": "ok",
            "candidates_count": len(candidates),
            "candidates": [c.model_dump() for c in candidates],
            "archive_saved_count": archive_saved_count,
            "archive_warnings": archive_warnings,
        }

    @router.get("")
    def list_opportunities(limit: int = 100):
        return repository.list_opportunity_candidates(limit)

    @router.get("/{candidate_id}")
    def get_opportunity(candidate_id: str):
        candidate = repository.get_candidate(candidate_id)
        if not candidate:
            return {"status": "error", "message": "candidate not found"}
        return candidate

    @router.post("/{candidate_id}/block")
    def block_opportunity(candidate_id: str):
        from uuid import uuid4

        repository.update_candidate_action_status(candidate_id, ActionStatus.BLOCKED)
        repository.save_audit_log(
            AuditLogEvent(
                event_id=f"evt_{uuid4().hex[:10]}",
                event_type="CANDIDATE_BLOCKED",
                object_type="OpportunityCandidate",
                object_id=candidate_id,
                payload={},
            )
        )
        return {"status": "ok", "candidate_id": candidate_id, "action_status": "BLOCKED"}

    return router
