from __future__ import annotations

import json
import subprocess
import sys
from datetime import timedelta
from http import HTTPStatus
from pathlib import Path

import pytest

from aars_market.api import make_handler
from aars_market.forward import ForwardObservationSettings, build_forward_observation
from aars_market.models import Candle, FundingRate
from aars_market.service import DashboardService
from aars_market.storage import MarketStore
from aars_market.trial import build_paper_trial_result
from tests.test_mil316 import START, SYMBOLS, _seed


def _eligible_trial(path: Path, *, total_bars: int = 300) -> tuple[MarketStore, str, dict]:
    store, _, proposal = _seed(path)
    trial = build_paper_trial_result(store, proposal, generated_at=START)
    assert trial["review_gate"]["disposition"] == "ELIGIBLE_FOR_EXTENDED_PAPER_OBSERVATION"
    trial_id = store.archive_paper_trial_result(trial)
    for symbol_index, symbol in enumerate(SYMBOLS):
        candles = []
        for index in range(220, total_bars):
            center = 100.0 + symbol_index * 15 + index * 0.025
            wave = (index % 16 - 8) * 0.18
            close = center + wave
            candles.append(Candle(
                symbol, "1h", START + timedelta(hours=index), center,
                max(center, close) + 0.4, min(center, close) - 0.4,
                close, 1000.0 + index,
            ))
        store.upsert_candles(candles, "forward-test")
        store.upsert_funding_rates(
            [
                FundingRate(
                    symbol, START + timedelta(hours=index), 0.0001,
                    100.0 + symbol_index * 15 + index * 0.025,
                )
                for index in range(224, total_bars, 8)
            ],
            "forward-test",
        )
    envelope = store.get_paper_trial_result(trial_id)
    assert envelope is not None
    return store, trial_id, envelope


def test_forward_observation_uses_only_unseen_bars_and_common_end(tmp_path: Path):
    store, trial_id, envelope = _eligible_trial(tmp_path / "market.sqlite")
    payload = build_forward_observation(
        store, envelope,
        settings=ForwardObservationSettings(minimum_forward_bars=24, confirmation_bars=168),
        generated_at=START,
    )

    assert payload["schema_version"] == "mil3.forward-observation.v1"
    assert payload["trial_id"] == trial_id
    assert payload["boundary"]["policy"] == "STRICTLY_AFTER_TRIAL_EVIDENCE_END"
    assert payload["boundary"]["historical_replay_included"] is False
    assert payload["boundary"]["warmup_context_affects_performance"] is False
    assert payload["results"]["forward_bars"] == 80
    assert all(item["forward_bars"] == 80 for item in payload["results"]["per_asset"])
    assert all(item["warmup_context_bars"] == 59 for item in payload["results"]["per_asset"])
    assert all(item["forward_start"] == (START + timedelta(hours=220)).isoformat() for item in payload["results"]["per_asset"])
    assert all(item["baseline"]["bars"] == 80 for item in payload["results"]["per_asset"])
    assert all(item["funding_coverage"]["status"] == "COMPLETE" for item in payload["results"]["per_asset"])
    assert payload["review_gate"]["disposition"] == "CONTINUE_FORWARD_OBSERVATION"
    assert payload["authority"] == {
        "observation_application_allowed": False,
        "automatic_strategy_change_allowed": False,
        "live_execution_allowed": False,
    }
    json.dumps(payload, allow_nan=False)


def test_forward_observation_fails_closed_on_history_and_funding_gaps(tmp_path: Path):
    store, _, envelope = _eligible_trial(tmp_path / "short.sqlite", total_bars=230)
    with pytest.raises(ValueError, match="insufficient forward history"):
        build_forward_observation(store, envelope)

    gapped, _, gapped_envelope = _eligible_trial(tmp_path / "gapped.sqlite")
    with gapped.connect() as conn:
        conn.execute(
            "DELETE FROM funding_rates WHERE symbol=? AND funding_time=?",
            ("BTCUSDT", (START + timedelta(hours=256)).isoformat()),
        )
    with pytest.raises(ValueError, match="status=GAPPED"):
        build_forward_observation(gapped, gapped_envelope)


def test_forward_observation_rejects_noneligible_trial(tmp_path: Path):
    store, _, envelope = _eligible_trial(tmp_path / "market.sqlite")
    unsafe = json.loads(json.dumps(envelope))
    unsafe["trial"]["review_gate"]["disposition"] = "CONTINUE_BASELINE"
    with pytest.raises(ValueError, match="not eligible"):
        build_forward_observation(store, unsafe)


def test_forward_archive_is_append_only_idempotent_and_lineage_chained(tmp_path: Path):
    store, trial_id, envelope = _eligible_trial(tmp_path / "market.sqlite")
    first = build_forward_observation(
        store, envelope, as_of=START + timedelta(hours=259), generated_at=START
    )
    first_id = store.archive_forward_observation(first)
    same = build_forward_observation(
        store, envelope, as_of=START + timedelta(hours=259), generated_at=START + timedelta(days=1)
    )
    assert store.archive_forward_observation(same) == first_id

    second = build_forward_observation(store, envelope, generated_at=START + timedelta(days=2))
    assert second["lineage"]["previous_observation_id"] == first_id
    assert second["lineage"]["previous_input_sha256"] == first["input_evidence"]["combined_sha256"]
    second_id = store.archive_forward_observation(second)
    assert second_id != first_id
    assert len(store.list_forward_observations(trial_id=trial_id)) == 2

    conflicting = json.loads(json.dumps(second))
    conflicting["review_gate"]["confirmation_bars_required"] = 999
    with pytest.raises(ValueError, match="different observation evidence"):
        store.archive_forward_observation(conflicting)

    backward = build_forward_observation(
        store, envelope, as_of=START + timedelta(hours=250), generated_at=START
    )
    with pytest.raises(ValueError, match="move backward"):
        store.archive_forward_observation(backward)

    tampered = json.loads(json.dumps(second))
    tampered["configuration"]["proposed"]["aars_max_abs_exposure"] = 9.0
    tampered["boundary"]["synchronized_forward_end"] = (START + timedelta(hours=301)).isoformat()
    with pytest.raises(ValueError, match="configuration differs from trial"):
        store.archive_forward_observation(tampered)

    crossed = json.loads(json.dumps(second))
    crossed["boundary"]["synchronized_forward_end"] = (START + timedelta(hours=301)).isoformat()
    crossed["results"]["per_asset"][0]["forward_start"] = (START + timedelta(hours=219)).isoformat()
    crossed["results"]["per_asset"][0]["forward_end"] = (START + timedelta(hours=301)).isoformat()
    crossed["results"]["per_asset"][1]["forward_end"] = (START + timedelta(hours=301)).isoformat()
    with pytest.raises(ValueError, match="crosses trial boundary"):
        store.archive_forward_observation(crossed)


def test_forward_stop_condition_overrides_confirmation(tmp_path: Path):
    store, _, envelope = _eligible_trial(tmp_path / "market.sqlite")
    strict = json.loads(json.dumps(envelope))
    strict["trial"]["configuration"]["settings"]["stop_max_drawdown"] = 0.0
    payload = build_forward_observation(store, strict)
    assert payload["stop_condition"]["triggered"] is True
    assert payload["review_gate"]["disposition"] == "STOP_FORWARD_OBSERVATION"


def test_forward_api_is_read_only(tmp_path: Path):
    store, trial_id, envelope = _eligible_trial(tmp_path / "market.sqlite")
    payload = build_forward_observation(store, envelope, generated_at=START)
    observation_id = store.archive_forward_observation(payload)
    handler_type = make_handler(DashboardService(store), tmp_path)
    handler = object.__new__(handler_type)

    handler.path = f"/api/v1/forward-observations?trial_id={trial_id}&limit=30"
    status, index = handler._api_payload()
    assert status == HTTPStatus.OK
    assert index["observations"][0]["observation_id"] == observation_id
    assert index["observation_application_allowed"] is False

    handler.path = f"/api/v1/forward-observations/{observation_id}"
    status, detail = handler._api_payload()
    assert status == HTTPStatus.OK
    assert detail["observation"]["trial_id"] == trial_id
    assert detail["live_execution_allowed"] is False

    handler.path = "/api/v1/forward-observations/missing"
    status, error = handler._api_payload()
    assert status == HTTPStatus.NOT_FOUND
    assert error == {"error": "forward observation not found"}


def test_forward_cli_is_the_explicit_local_write_path(tmp_path: Path):
    database = tmp_path / "market.sqlite"
    store, trial_id, _ = _eligible_trial(database)
    runner = Path(__file__).parents[1] / "run_forward_observation.py"
    completed = subprocess.run(
        [sys.executable, str(runner), "--db", str(database), "--trial-id", trial_id],
        check=True, capture_output=True, text=True,
    )
    assert "execution_mode=PAPER_ONLY" in completed.stdout
    assert "forward_only=true" in completed.stdout
    assert "observation_application_allowed=false" in completed.stdout
    assert "automatic_strategy_change_allowed=false" in completed.stdout
    assert "live_execution_allowed=false" in completed.stdout
    assert len(store.list_forward_observations(trial_id=trial_id)) == 1


def test_forward_ui_is_read_only_and_keeps_boundary_visible():
    ui_root = Path(__file__).parents[1] / "ui"
    html = (ui_root / "index.html").read_text(encoding="utf-8")
    javascript = (ui_root / "app.js").read_text(encoding="utf-8")
    css = (ui_root / "styles.css").read_text(encoding="utf-8")

    assert 'id="forward-observation-status"' in html
    assert 'id="forward-observation-comparison"' in html
    assert 'id="forward-observation-boundary"' in html
    assert 'id="forward-observation-lineage"' in html
    assert "STRICTLY AFTER TRIAL" in html
    assert "APPLICATION DISALLOWED" in html
    assert "/api/v1/forward-observations?limit=30" in javascript
    assert "/api/v1/forward-observations/${encodeURIComponent(latest.observation_id)}" in javascript
    assert "STRICTLY_AFTER_TRIAL_EVIDENCE_END" in javascript
    assert "forward observation did not preserve authority locks" in javascript
    assert "NO RESULT APPLIES A CONFIGURATION" in javascript
    assert '.forward-observation-card[data-status="STOP_FORWARD_OBSERVATION"]' in css
    assert '.forward-observation-card[data-status="CONTINUE_FORWARD_OBSERVATION"]' in css
