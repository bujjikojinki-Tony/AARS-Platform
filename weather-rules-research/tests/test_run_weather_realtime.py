from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
for path in (SRC, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import run_weather_realtime as realtime


def test_normalize_market_question_target_date() -> None:
    assert realtime._normalize_market_question_target_date(
        "Highest temperature in Shanghai on April 20?"
    ) == "Apr 20"


def test_sync_station_map_writes_canonical_payload(tmp_path, monkeypatch) -> None:
    canonical = tmp_path / "manual_station_map.json"
    target = tmp_path / "sample_station_map.json"
    canonical.write_text(
        json.dumps(
            [
                {
                    "canonical_location": "Shanghai",
                    "selected_station": {
                        "station_name": "Shanghai Pudong International Airport",
                        "nws_station_id": "ZSPD",
                        "cdo_station_id": None,
                        "latitude": 31.1434,
                        "longitude": 121.8052,
                        "timezone": "Asia/Shanghai",
                        "source": "wunderground:zspd",
                    },
                    "aliases": ["Shanghai Pudong International Airport"],
                    "mapping_method": "manual_whitelist",
                    "mapping_confidence": 0.96,
                }
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(realtime, "CANONICAL_STATION_MAP_JSON", canonical)
    monkeypatch.setattr(realtime, "STATION_MAP_JSON", target)

    synced_path = realtime._sync_station_map()

    assert synced_path == target
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload[0]["canonical_location"] == "Shanghai"


def test_startup_self_check_and_sync_returns_snapshot(monkeypatch, tmp_path) -> None:
    canonical = tmp_path / "manual_station_map.json"
    target = tmp_path / "sample_station_map.json"
    canonical.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(realtime, "CANONICAL_STATION_MAP_JSON", canonical)
    monkeypatch.setattr(realtime, "STATION_MAP_JSON", target)

    async def fake_poll_once(live_market=None):
        return {
            "market_id": "m1",
            "target_date": "Apr 20",
            "source_mode": "Target-date forecast unavailable",
            "source_path": "not_found",
        }

    monkeypatch.setattr(realtime, "poll_once", fake_poll_once)

    result = asyncio.run(realtime.startup_self_check_and_sync(live_market={"market_id": "m1"}))

    assert result["station_map_synced"] is True
    assert result["snapshot_refreshed"] is True
    assert result["snapshot"]["target_date"] == "Apr 20"
