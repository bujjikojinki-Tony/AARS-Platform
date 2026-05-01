from __future__ import annotations

import sqlite3

from fastapi.testclient import TestClient

from backend.app_factory import create_app
from backend.calibration_memory.backtest_memory_builder import BacktestMemoryBuilder
from backend.calibration_memory.calibration_sample_builder import CalibrationSampleBuilder
from backend.models.calibration_memory import CalibrationSample
from backend.models.calibration_memory import HypotheticalAction
from backend.models.calibration_memory import HypotheticalResult
from backend.models.calibration_memory import ResolvedOutcomeForMemory
from backend.storage.db import init_db
from backend.storage.repositories import Repository


def make_client(tmp_path) -> TestClient:
    app = create_app(
        db_path=str(tmp_path / "pwb05.sqlite"),
        allow_network=False,
        allow_polymarket_network=False,
        market_source_mode="MOCK_ONLY",
        archive_weather_on_probability_build=True,
    )
    return TestClient(app)


def make_sample(
    *,
    market_id: str = "m1",
    market_probability: float = 0.52,
    model_probability: float = 0.61,
    actual_outcome_value: float = 1.0,
    resolved_outcome: str = "YES",
) -> CalibrationSample:
    return CalibrationSample(
        calibration_sample_id="cs_test",
        market_id=market_id,
        snapshot_archive_id="msa_1",
        weather_view_archive_id="wva_1",
        weather_forecast_archive_id="wfa_1",
        probability_run_id="run_1",
        outcome_resolution_id="orr_1",
        engine_id="gaussian_v0",
        market_probability=market_probability,
        model_probability=model_probability,
        actual_outcome_value=actual_outcome_value,
        model_brier_score=(model_probability - actual_outcome_value) ** 2,
        market_brier_score=(market_probability - actual_outcome_value) ** 2,
        model_absolute_error=abs(model_probability - actual_outcome_value),
        market_absolute_error=abs(market_probability - actual_outcome_value),
        model_beats_market=(model_probability - actual_outcome_value) ** 2
        < (market_probability - actual_outcome_value) ** 2,
        resolved_outcome=resolved_outcome,
        sample_eligibility="ELIGIBLE",
        sample_status="READY",
    )


def get_candidate_count(client: TestClient) -> int:
    payload = client.get("/api/history/candidates").json()
    if isinstance(payload, list):
        return len(payload)
    return len(payload.get("items") or payload.get("candidates") or [])


def prepare_market_memory_inputs(client: TestClient, market_id: str = "tokyo_weather_market") -> str:
    client.post(
        "/api/snapshots/archive",
        json={
            "market_id": market_id,
            "question": "Will Tokyo high temperature exceed 30C on June 1?",
            "yes_price": 0.52,
            "no_price": 0.48,
            "liquidity": 1000,
            "spread": 0.03,
            "source": "mock",
            "market_source_mode": "MOCK_ONLY",
            "archive_reason": "MANUAL_CAPTURE",
        },
    )
    client.post(
        "/api/weather/probability",
        json={
            "market_id": market_id,
            "question": "Will Tokyo high temperature exceed 30C on June 1?",
            "yes_price": 0.52,
            "no_price": 0.48,
            "liquidity": 1000,
            "spread": 0.03,
        },
    )
    compare = client.post(f"/api/probability/compare/{market_id}").json()
    assert compare["status"] == "ok"
    actual = client.post(
        "/api/outcomes/weather-actual",
        json={
            "market_id": market_id,
            "city": "Tokyo",
            "target_date": "2026-06-01",
            "source": "MANUAL",
            "metric": "temperature_high",
            "unit": "C",
            "actual_value": 31.2,
        },
    ).json()
    resolved = client.post(
        "/api/outcomes/resolve-from-weather",
        json={"market_id": market_id, "weather_actual_id": actual["record"]["weather_actual_id"]},
    ).json()
    assert resolved["status"] == "ok"
    return actual["record"]["weather_actual_id"]


def test_models_serialize():
    sample = make_sample()
    dumped = sample.model_dump(mode="json")
    assert dumped["resolved_outcome"] == "YES"
    assert dumped["sample_status"] == "READY"
    assert dumped["model_beats_market"] is True


def test_tables_created(tmp_path):
    db_path = str(tmp_path / "memory.sqlite")
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('calibration_samples','backtest_memory_records')"
            ).fetchall()
        }
    assert "calibration_samples" in tables
    assert "backtest_memory_records" in tables


def test_repository_save_list_query_summary(tmp_path):
    db_path = str(tmp_path / "repo.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    sample = make_sample()
    repo.save_calibration_sample(sample)
    backtest = BacktestMemoryBuilder(repo).build_from_sample(sample, edge_threshold=0.05)
    assert len(repo.list_calibration_samples()) == 1
    assert len(repo.list_backtest_memory_records()) == 1
    assert repo.get_calibration_sample_by_id(sample.calibration_sample_id) is not None
    assert repo.get_backtest_memory_record_by_id(backtest.backtest_memory_id) is not None
    summary = repo.get_calibration_memory_summary()
    assert summary.calibration_samples == 1
    assert summary.backtest_memory_records == 1
    assert summary.by_sample_status["READY"] == 1
    assert summary.by_backtest_status["READY"] == 1


def test_eligibility_missing_and_complete(tmp_path):
    db_path = str(tmp_path / "eligibility.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    builder = CalibrationSampleBuilder(repo)
    missing = builder.check_eligibility("m_missing")
    assert missing["eligibility"] in {"PARTIAL", "INELIGIBLE"}
    assert missing["missing_components"]

    client = make_client(tmp_path / "complete")
    prepare_market_memory_inputs(client, market_id="m_complete")
    repo2 = Repository(str((tmp_path / "complete") / "pwb05.sqlite"))
    complete = CalibrationSampleBuilder(repo2).check_eligibility("m_complete")
    assert complete["eligibility"] == "ELIGIBLE"
    assert complete["missing_components"] == []


def test_brier_scores_and_model_beats_market_yes_no(tmp_path):
    db_path = str(tmp_path / "builder.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    yes = make_sample(market_probability=0.52, model_probability=0.90, actual_outcome_value=1.0, resolved_outcome="YES")
    repo.save_calibration_sample(yes)
    row = repo.get_calibration_sample_by_id("cs_test")
    assert row is not None

    sample_yes = make_sample(market_probability=0.52, model_probability=0.90, actual_outcome_value=1.0, resolved_outcome="YES")
    assert sample_yes.model_brier_score == (0.90 - 1.0) ** 2
    assert sample_yes.market_brier_score == (0.52 - 1.0) ** 2
    assert sample_yes.model_beats_market is True

    sample_no = make_sample(market_probability=0.20, model_probability=0.80, actual_outcome_value=0.0, resolved_outcome="NO")
    assert sample_no.model_brier_score == (0.80 - 0.0) ** 2
    assert sample_no.market_brier_score == (0.20 - 0.0) ** 2
    assert sample_no.model_beats_market is False


def test_hypothetical_backtest_rules_pass(tmp_path):
    db_path = str(tmp_path / "backtest.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    builder = BacktestMemoryBuilder(repo, edge_threshold=0.05)

    take_yes = builder.build_from_sample(
        make_sample(market_probability=0.52, model_probability=0.70, actual_outcome_value=1.0, resolved_outcome="YES")
    )
    assert take_yes.hypothetical_action == HypotheticalAction.TAKE_YES
    assert take_yes.hypothetical_result == HypotheticalResult.WIN

    take_no = builder.build_from_sample(
        make_sample(market_probability=0.52, model_probability=0.30, actual_outcome_value=0.0, resolved_outcome="NO")
    )
    assert take_no.hypothetical_action == HypotheticalAction.TAKE_NO
    assert take_no.hypothetical_result == HypotheticalResult.WIN

    skip = builder.build_from_sample(
        make_sample(market_probability=0.52, model_probability=0.54, actual_outcome_value=1.0, resolved_outcome="YES")
    )
    assert skip.hypothetical_action == HypotheticalAction.SKIP
    assert skip.hypothetical_result == HypotheticalResult.PUSH


def test_build_apis_do_not_create_candidates_or_trigger_execution(tmp_path):
    client = make_client(tmp_path)
    prepare_market_memory_inputs(client)
    before = get_candidate_count(client)
    sample = client.post("/api/calibration-memory/build-sample", json={"market_id": "tokyo_weather_market"}).json()
    backtest = client.post("/api/calibration-memory/build-backtest", json={"market_id": "tokyo_weather_market"}).json()
    build_all = client.post("/api/calibration-memory/build-all-eligible", json={}).json()
    after = get_candidate_count(client)

    assert sample["status"] == "ok"
    assert backtest["status"] == "ok"
    assert build_all["status"] == "ok"
    assert after == before
    for payload in [sample, backtest, build_all]:
        assert payload["safety"]["probability_engine_called"] is False
        assert payload["safety"]["strategy_runner_called"] is False
        assert payload["safety"]["candidates_created"] is False
        assert payload["safety"]["simulation_triggered"] is False
        assert payload["safety"]["execution_triggered"] is False
        assert payload["safety"]["promotion_triggered"] is False
        assert payload["safety"]["active_engine_changed"] is False


def test_memory_api_shapes(tmp_path):
    client = make_client(tmp_path)
    prepare_market_memory_inputs(client, market_id="m_api")
    client.post("/api/calibration-memory/build-sample", json={"market_id": "m_api"})
    client.post("/api/calibration-memory/build-backtest", json={"market_id": "m_api"})

    assert client.get("/api/calibration-memory/summary").json()["status"] == "ok"
    assert client.get("/api/calibration-memory/samples").json()["status"] == "ok"
    assert client.get("/api/calibration-memory/backtests").json()["status"] == "ok"
    assert client.get("/api/calibration-memory/eligibility/m_api").json()["status"] == "ok"
    bundle = client.get("/api/calibration-memory/market/m_api").json()
    assert bundle["status"] == "ok"
    assert bundle["market_id"] == "m_api"


def test_live_execute_still_rejected(tmp_path):
    client = make_client(tmp_path)
    prepare_market_memory_inputs(client, market_id="m_live")
    client.post("/api/calibration-memory/build-sample", json={"market_id": "m_live"})
    response = client.post("/api/settings/mode", json={"mode": "LIVE_EXECUTE"})
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "error"
    assert "LIVE_EXECUTE" in data["message"]
