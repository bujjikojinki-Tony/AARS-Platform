from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_polymarket_realtime.py"


def load_script_module():
    spec = importlib.util.spec_from_file_location("run_polymarket_realtime", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_select_preferred_market_prefers_priced_row_over_pinned_null() -> None:
    module = load_script_module()
    priced_row = {
        "market_id": "priced",
        "market_family": "station_temperature",
        "updated_at": "2026-04-20T00:00:00+00:00",
        "yes_price": 0.61,
        "no_price": 0.39,
        "market_probability": 0.61,
    }
    pinned_null_row = {
        "market_id": "pinned",
        "market_family": "station_temperature",
        "updated_at": "2026-04-20T01:00:00+00:00",
        "yes_price": None,
        "no_price": None,
        "market_probability": None,
    }

    selected = module.select_preferred_market(
        [pinned_null_row, priced_row],
        pinned_market_id="pinned",
        pinned_family="station_temperature",
    )

    assert selected is not None
    assert selected["market_id"] == "priced"


def test_select_startup_simple_snapshot_uses_existing_priced_snapshot(tmp_path: Path) -> None:
    module = load_script_module()
    existing_snapshot = {
        "market_id": "existing_priced",
        "market_family": "station_temperature",
        "updated_at": "2026-04-20T01:00:00+00:00",
        "yes_price": 0.67,
        "no_price": 0.33,
        "market_probability": 0.67,
    }
    (tmp_path / "market_realtime_simple_station_temperature.json").write_text(
        json.dumps(existing_snapshot),
        encoding="utf-8",
    )
    initial_family_snapshots = {
        "station_temperature": {
            "market_id": "initial_null",
            "market_family": "station_temperature",
            "updated_at": "2026-04-20T00:00:00+00:00",
            "yes_price": None,
            "no_price": None,
            "market_probability": None,
        }
    }

    selected = module.select_startup_simple_snapshot(
        initial_family_snapshots=initial_family_snapshots,
        output_dir=tmp_path,
        pinned_market_id=None,
        pinned_family="station_temperature",
    )

    assert selected is not None
    assert selected["market_id"] == "existing_priced"
