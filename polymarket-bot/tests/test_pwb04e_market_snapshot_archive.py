from __future__ import annotations

import sqlite3
from fastapi.testclient import TestClient

from backend.app_factory import create_app
from backend.archive.market_snapshot_archive_service import MarketSnapshotArchiveService
from backend.models.core import MarketSnapshot
from backend.models.polymarket import MarketSourceMode
from backend.models.snapshot_archive import MarketSnapshotArchiveRecord
from backend.models.snapshot_archive import SnapshotArchiveReason
from backend.storage.db import init_db
from backend.storage.repositories import Repository


def _sample_record(
    *,
    snapshot_archive_id: str = "snap_1",
    market_id: str = "m1",
    archived_at: str = "2026-04-30T00:00:00Z",
    source: str = "mock",
    archive_reason: SnapshotArchiveReason = SnapshotArchiveReason.SCAN_CAPTURE,
):
    return MarketSnapshotArchiveRecord(
        snapshot_archive_id=snapshot_archive_id,
        market_id=market_id,
        source=source,
        question="Will Tokyo high temperature exceed 30C on June 1?",
        yes_price=0.52,
        no_price=0.48,
        liquidity=1000.0,
        spread=0.04,
        fetched_at="2026-04-30T00:00:00Z",
        archived_at=archived_at,
        market_source_mode=MarketSourceMode.MOCK_ONLY,
        raw_ref="raw://market/m1",
        metadata={"batch": 1},
        archive_reason=archive_reason,
    )


def test_snapshot_archive_model_serializes():
    record = _sample_record()
    dumped = record.model_dump(mode="json")

    assert dumped["snapshot_archive_id"] == "snap_1"
    assert dumped["market_id"] == "m1"
    assert dumped["market_source_mode"] == "MOCK_ONLY"
    assert dumped["archive_reason"] == "SCAN_CAPTURE"


def test_snapshot_archive_table_created(tmp_path):
    db_path = str(tmp_path / "pwb04e.sqlite")
    init_db(db_path)

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = 'market_snapshot_archive'
            """
        ).fetchone()

    assert row is not None


def test_archive_single_snapshot(tmp_path):
    db_path = str(tmp_path / "single.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    repo.save_market_snapshot_archive_record(_sample_record())

    rows = repo.list_market_snapshot_archive()
    assert len(rows) == 1
    assert rows[0]["snapshot_archive_id"] == "snap_1"
    assert rows[0]["metadata"] == {"batch": 1}


def test_archive_service_single_snapshot(tmp_path):
    db_path = str(tmp_path / "service_single.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    service = MarketSnapshotArchiveService(repo)

    record = service.archive_snapshot(
        snapshot=MarketSnapshot(
            market_id="m1",
            question="Will Tokyo high temperature exceed 30C on June 1?",
            yes_price=0.52,
            no_price=0.48,
            liquidity=1000.0,
            spread=0.04,
            source="mock",
            fetched_at="2026-04-30T00:00:00Z",
        ),
        market_source_mode=MarketSourceMode.MOCK_ONLY,
        archive_reason=SnapshotArchiveReason.MANUAL_CAPTURE,
        raw_ref="raw://market/m1",
        metadata={"capture": "manual"},
    )

    assert record.market_id == "m1"
    assert repo.get_market_snapshot_archive_summary().total_snapshots == 1


def test_archive_multiple_snapshots(tmp_path):
    db_path = str(tmp_path / "multiple.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    repo.save_market_snapshot_archive_records(
        [
            _sample_record(snapshot_archive_id="snap_1"),
            _sample_record(snapshot_archive_id="snap_2", market_id="m2"),
        ]
    )

    rows = repo.list_market_snapshot_archive(limit=10)
    assert len(rows) == 2


def test_archive_service_multiple_snapshots(tmp_path):
    db_path = str(tmp_path / "service_multi.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    service = MarketSnapshotArchiveService(repo)

    records = service.archive_snapshots(
        snapshots=[
            MarketSnapshot(
                market_id="m1",
                question="Will Tokyo high temperature exceed 30C on June 1?",
                yes_price=0.52,
                no_price=0.48,
                liquidity=1000.0,
                spread=0.04,
                source="mock",
                fetched_at="2026-04-30T00:00:00Z",
            ),
            MarketSnapshot(
                market_id="m2",
                question="Will Osaka high temperature exceed 28C on June 1?",
                yes_price=0.51,
                no_price=0.49,
                liquidity=800.0,
                spread=0.02,
                source="polymarket",
                fetched_at="2026-04-30T00:10:00Z",
            ),
        ],
        market_source_mode=MarketSourceMode.HYBRID,
        archive_reason=SnapshotArchiveReason.PREVIEW_CAPTURE,
    )

    assert len(records) == 2
    assert repo.get_market_snapshot_archive_summary().unique_markets == 2


def test_market_snapshot_series(tmp_path):
    db_path = str(tmp_path / "series.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    repo.save_market_snapshot_archive_records(
        [
            _sample_record(snapshot_archive_id="snap_1", archived_at="2026-04-30T00:00:00Z"),
            _sample_record(snapshot_archive_id="snap_2", archived_at="2026-04-30T01:00:00Z"),
        ]
    )

    series = repo.get_market_snapshot_series("m1")
    assert series.market_id == "m1"
    assert series.count == 2
    assert series.first_archived_at == "2026-04-30T00:00:00Z"
    assert series.last_archived_at == "2026-04-30T01:00:00Z"


def test_snapshot_archive_summary(tmp_path):
    db_path = str(tmp_path / "summary.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    repo.save_market_snapshot_archive_records(
        [
            _sample_record(snapshot_archive_id="snap_1", source="mock"),
            _sample_record(
                snapshot_archive_id="snap_2",
                market_id="m2",
                source="polymarket",
                archive_reason=SnapshotArchiveReason.SYNC_CAPTURE,
            ),
        ]
    )

    summary = repo.get_market_snapshot_archive_summary()
    assert summary.total_snapshots == 2
    assert summary.unique_markets == 2
    assert summary.by_source["mock"] == 1
    assert summary.by_source["polymarket"] == 1
    assert summary.by_archive_reason["SCAN_CAPTURE"] == 1
    assert summary.by_archive_reason["SYNC_CAPTURE"] == 1


def make_client(tmp_path, mode="MOCK_ONLY", allow_polymarket_network=False):
    app = create_app(
        db_path=str(tmp_path / f"pwb04e_{mode}.sqlite"),
        allow_network=False,
        allow_polymarket_network=allow_polymarket_network,
        market_source_mode=mode,
    )
    return TestClient(app)


def test_archive_current_source_api(tmp_path):
    client = make_client(tmp_path, mode="HYBRID", allow_polymarket_network=False)

    response = client.post("/api/snapshots/archive/current-source", json={"limit": 10})
    data = response.json()
    summary = client.get("/api/snapshots/archive/summary").json()

    assert response.status_code == 200
    assert data["status"] == "ok"
    assert data["archived_count"] >= 1
    assert data["candidate_count_unchanged"] is True
    assert summary["summary"]["total_snapshots"] >= 1


def test_archive_current_source_does_not_create_candidates(tmp_path):
    client = make_client(tmp_path, mode="HYBRID", allow_polymarket_network=False)

    before = client.get("/api/history/candidates").json()
    response = client.post("/api/snapshots/archive/current-source", json={"limit": 10}).json()
    after = client.get("/api/history/candidates").json()

    assert response["status"] == "ok"
    assert len(before) == len(after)


def test_snapshot_archive_api_manual_archive_and_queries(tmp_path):
    client = make_client(tmp_path)

    create = client.post(
        "/api/snapshots/archive",
        json={
            "snapshot": {
                "market_id": "m_manual",
                "question": "Will it rain in Shanghai?",
                "yes_price": 0.55,
                "no_price": 0.45,
                "liquidity": 900.0,
                "spread": 0.03,
                "source": "mock",
                "fetched_at": "2026-04-30T00:00:00Z",
            },
            "market_source_mode": "MOCK_ONLY",
            "archive_reason": "MANUAL_CAPTURE",
        },
    )
    recent = client.get("/api/snapshots/archive?limit=10")
    summary = client.get("/api/snapshots/archive/summary")
    series = client.get("/api/snapshots/archive/market/m_manual?limit=10")

    assert create.status_code == 200
    assert create.json()["status"] == "ok"
    assert recent.json()["status"] == "ok"
    assert summary.json()["summary"]["total_snapshots"] == 1
    assert series.json()["series"]["market_id"] == "m_manual"


def test_sync_weather_markets_archive_optional(tmp_path):
    client = make_client(tmp_path, mode="HYBRID", allow_polymarket_network=False)
    before = client.get("/api/history/candidates").json()

    response = client.post(
        "/api/polymarket/sync-weather-markets",
        json={"limit": 10, "archive": True},
    )
    data = response.json()
    after = client.get("/api/history/candidates").json()
    summary = client.get("/api/snapshots/archive/summary").json()

    assert response.status_code == 200
    assert data["status"] == "ok"
    assert data["archive_saved_count"] >= 1
    assert len(before) == len(after)
    assert summary["summary"]["total_snapshots"] >= 1


def test_snapshot_archive_ui_api(tmp_path):
    client = make_client(tmp_path)
    client.post(
        "/api/snapshots/archive",
        json={
            "snapshot": {
                "market_id": "m_ui",
                "question": "Will it snow?",
                "yes_price": 0.4,
                "no_price": 0.6,
                "liquidity": 500.0,
                "spread": 0.02,
                "source": "mock",
                "fetched_at": "2026-04-30T00:00:00Z",
            },
            "market_source_mode": "MOCK_ONLY",
            "archive_reason": "MANUAL_CAPTURE",
        },
    )

    summary = client.get("/api/snapshots/archive/summary").json()
    recent = client.get("/api/snapshots/archive?limit=5").json()
    series = client.get("/api/snapshots/archive/market/m_ui?limit=5").json()

    assert summary["status"] == "ok"
    assert recent["status"] == "ok"
    assert series["status"] == "ok"


def test_archive_on_scan_capture(tmp_path):
    client = make_client(tmp_path, mode="HYBRID", allow_polymarket_network=False)

    response = client.post("/api/opportunities/scan?archive_on_scan=true")
    data = response.json()
    summary = client.get("/api/snapshots/archive/summary").json()

    assert data["status"] == "ok"
    assert data["archive_saved_count"] >= 1
    assert summary["summary"]["total_snapshots"] >= 1


def test_live_execute_still_rejected(tmp_path):
    client = make_client(tmp_path, mode="HYBRID", allow_polymarket_network=False)

    response = client.post("/api/settings/mode", json={"mode": "LIVE_EXECUTE"})
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "error"
    assert "LIVE_EXECUTE" in data["message"]
