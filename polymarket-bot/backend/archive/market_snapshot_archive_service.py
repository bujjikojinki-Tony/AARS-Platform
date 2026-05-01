from __future__ import annotations

from uuid import uuid4

from backend.models.core import MarketSnapshot
from backend.models.polymarket import MarketSourceMode
from backend.models.snapshot_archive import MarketSnapshotArchiveRecord
from backend.models.snapshot_archive import MarketSnapshotSeries
from backend.models.snapshot_archive import SnapshotArchiveReason
from backend.models.snapshot_archive import SnapshotArchiveSummary


class MarketSnapshotArchiveService:
    def __init__(self, repository):
        self.repository = repository

    def archive_snapshot(
        self,
        snapshot: MarketSnapshot,
        market_source_mode: str | MarketSourceMode,
        archive_reason: str | SnapshotArchiveReason,
        raw_ref: str | None = None,
        metadata: dict | None = None,
    ) -> MarketSnapshotArchiveRecord:
        record = MarketSnapshotArchiveRecord(
            snapshot_archive_id=f"snaparch_{uuid4().hex[:12]}",
            market_id=snapshot.market_id,
            source=snapshot.source or "unknown",
            question=snapshot.question,
            yes_price=snapshot.yes_price,
            no_price=snapshot.no_price,
            liquidity=snapshot.liquidity,
            spread=snapshot.spread,
            fetched_at=snapshot.fetched_at,
            market_source_mode=self._normalize_market_source_mode(market_source_mode),
            raw_ref=raw_ref,
            metadata=metadata or {},
            archive_reason=self._normalize_archive_reason(archive_reason),
        )
        self.repository.save_market_snapshot_archive_record(record)
        return record

    def archive_snapshots(
        self,
        snapshots: list[MarketSnapshot],
        market_source_mode: str | MarketSourceMode,
        archive_reason: str | SnapshotArchiveReason,
        raw_ref: str | None = None,
        metadata: dict | None = None,
    ) -> list[MarketSnapshotArchiveRecord]:
        records: list[MarketSnapshotArchiveRecord] = []
        normalized_mode = self._normalize_market_source_mode(market_source_mode)
        normalized_reason = self._normalize_archive_reason(archive_reason)
        for snapshot in snapshots:
            records.append(
                MarketSnapshotArchiveRecord(
                    snapshot_archive_id=f"snaparch_{uuid4().hex[:12]}",
                    market_id=snapshot.market_id,
                    source=snapshot.source or "unknown",
                    question=snapshot.question,
                    yes_price=snapshot.yes_price,
                    no_price=snapshot.no_price,
                    liquidity=snapshot.liquidity,
                    spread=snapshot.spread,
                    fetched_at=snapshot.fetched_at,
                    market_source_mode=normalized_mode,
                    raw_ref=raw_ref,
                    metadata=metadata or {},
                    archive_reason=normalized_reason,
                )
            )
        self.repository.save_market_snapshot_archive_records(records)
        return records

    def list_recent_snapshots(
        self,
        limit: int = 100,
        source: str | None = None,
        archive_reason: str | SnapshotArchiveReason | None = None,
    ) -> list[dict]:
        return self.repository.list_market_snapshot_archive(
            limit=limit,
            source=source,
            archive_reason=archive_reason,
        )

    def get_market_snapshot_series(
        self,
        market_id: str,
        limit: int = 500,
    ) -> MarketSnapshotSeries:
        return self.repository.get_market_snapshot_series(market_id, limit=limit)

    def get_summary(self) -> SnapshotArchiveSummary:
        return self.repository.get_market_snapshot_archive_summary()

    def _normalize_market_source_mode(
        self,
        value: str | MarketSourceMode,
    ) -> MarketSourceMode:
        if isinstance(value, MarketSourceMode):
            return value
        return MarketSourceMode(str(value))

    def _normalize_archive_reason(
        self,
        value: str | SnapshotArchiveReason,
    ) -> SnapshotArchiveReason:
        if isinstance(value, SnapshotArchiveReason):
            return value
        return SnapshotArchiveReason(str(value))
