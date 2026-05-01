from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel
from pydantic import Field

from backend.models.core import now_iso
from backend.models.polymarket import MarketSourceMode


class SnapshotArchiveReason(str, Enum):
    SCAN_CAPTURE = "SCAN_CAPTURE"
    SYNC_CAPTURE = "SYNC_CAPTURE"
    MANUAL_CAPTURE = "MANUAL_CAPTURE"
    PREVIEW_CAPTURE = "PREVIEW_CAPTURE"


class MarketSnapshotArchiveRecord(BaseModel):
    snapshot_archive_id: str
    market_id: str
    source: str = "unknown"
    question: str
    yes_price: float
    no_price: float
    liquidity: float
    spread: float
    fetched_at: str | None = None
    archived_at: str = Field(default_factory=now_iso)
    market_source_mode: MarketSourceMode = MarketSourceMode.MOCK_ONLY
    raw_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    archive_reason: SnapshotArchiveReason


class MarketSnapshotSeries(BaseModel):
    market_id: str
    count: int
    first_archived_at: str | None = None
    last_archived_at: str | None = None
    snapshots: list[MarketSnapshotArchiveRecord] = Field(default_factory=list)


class SnapshotArchiveSummary(BaseModel):
    total_snapshots: int
    unique_markets: int
    by_source: dict[str, int] = Field(default_factory=dict)
    by_archive_reason: dict[str, int] = Field(default_factory=dict)
    latest_archived_at: str | None = None
