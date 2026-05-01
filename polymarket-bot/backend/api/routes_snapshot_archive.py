from __future__ import annotations

from fastapi import APIRouter

from backend.archive.market_snapshot_archive_service import MarketSnapshotArchiveService
from backend.models.core import MarketSnapshot
from backend.models.snapshot_archive import SnapshotArchiveReason


def create_snapshot_archive_router(services) -> APIRouter:
    router = APIRouter(prefix="/api/snapshots", tags=["snapshot-archive"])
    archive_service = MarketSnapshotArchiveService(services.repository)

    @router.get("/archive")
    def get_snapshot_archive(
        limit: int = 100,
        source: str | None = None,
        archive_reason: str | None = None,
    ):
        items = archive_service.list_recent_snapshots(
            limit=limit,
            source=source,
            archive_reason=archive_reason,
        )
        return {
            "status": "ok",
            "items": items,
        }

    @router.get("/archive/summary")
    def get_snapshot_archive_summary():
        summary = archive_service.get_summary()
        return {
            "status": "ok",
            "summary": summary.model_dump(mode="json"),
        }

    @router.get("/archive/market/{market_id}")
    def get_snapshot_archive_market_series(market_id: str, limit: int = 500):
        series = archive_service.get_market_snapshot_series(market_id, limit=limit)
        return {
            "status": "ok",
            "series": series.model_dump(mode="json"),
        }

    @router.post("/archive")
    def post_snapshot_archive(payload: dict):
        snapshot_payload = payload.get("snapshot") if isinstance(payload.get("snapshot"), dict) else payload
        snapshot = MarketSnapshot(**snapshot_payload)
        record = archive_service.archive_snapshot(
            snapshot=snapshot,
            market_source_mode=payload.get("market_source_mode") or services.market_source_mode.value,
            archive_reason=payload.get("archive_reason") or SnapshotArchiveReason.MANUAL_CAPTURE.value,
            raw_ref=payload.get("raw_ref"),
            metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else None,
        )
        return {
            "status": "ok",
            "record": record.model_dump(mode="json"),
        }

    @router.post("/archive/current-source")
    def post_snapshot_archive_current_source(payload: dict | None = None):
        payload = payload or {}
        limit = int(payload.get("limit") or 50)
        warnings: list[str] = []
        before_candidates = len(services.repository.list_table("opportunity_candidates", limit=1000))
        snapshots = _fetch_current_source_snapshots(services.market_source, limit)
        records = []
        try:
            records = archive_service.archive_snapshots(
                snapshots=snapshots,
                market_source_mode=services.market_source_mode,
                archive_reason=payload.get("archive_reason") or SnapshotArchiveReason.PREVIEW_CAPTURE.value,
                raw_ref=payload.get("raw_ref"),
                metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else None,
            )
        except Exception as exc:
            warnings.append(f"archive-current-source failed safely: {exc}")
        after_candidates = len(services.repository.list_table("opportunity_candidates", limit=1000))
        return {
            "status": "ok",
            "archived_count": len(records),
            "records": [record.model_dump(mode="json") for record in records],
            "candidate_count_unchanged": before_candidates == after_candidates,
            "warnings": warnings,
        }

    return router


def _fetch_current_source_snapshots(market_source, limit: int) -> list[MarketSnapshot]:
    try:
        snapshots = market_source.fetch_markets(limit=limit)
    except TypeError:
        snapshots = market_source.fetch_markets()
    return list(snapshots)[:limit]
