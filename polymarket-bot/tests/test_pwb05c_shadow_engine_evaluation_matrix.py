from __future__ import annotations

import sqlite3

from fastapi.testclient import TestClient

from backend.app_factory import create_app
from backend.deb_shadow.deb_shadow_service import DebShadowService
from backend.emos_shadow.emos_shadow_service import EmosShadowService
from backend.models.calibration_memory import CalibrationSample
from backend.models.shadow_engine_evaluation import BestShadowEngine
from backend.models.shadow_engine_evaluation import ShadowEngineEvaluationRecord
from backend.models.shadow_engine_evaluation import ShadowEngineEvaluationStatus
from backend.shadow_engine_evaluation.shadow_engine_evaluation_service import (
    ShadowEngineEvaluationService,
)
from backend.storage.db import init_db
from backend.storage.repositories import Repository


def make_client(tmp_path) -> TestClient:
    app = create_app(
        db_path=str(tmp_path / "pwb05c.sqlite"),
        allow_network=False,
        allow_polymarket_network=False,
        market_source_mode="MOCK_ONLY",
        archive_weather_on_probability_build=True,
    )
    return TestClient(app)


def make_sample(
    *,
    calibration_sample_id: str,
    market_id: str,
    market_probability: float,
    model_probability: float,
    actual_outcome_value: float,
) -> CalibrationSample:
    return CalibrationSample(
        calibration_sample_id=calibration_sample_id,
        market_id=market_id,
        snapshot_archive_id="msa_1",
        weather_view_archive_id="wva_1",
        weather_forecast_archive_id="wfa_1",
        probability_run_id=f"run_{calibration_sample_id}",
        outcome_resolution_id=f"orr_{calibration_sample_id}",
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
        resolved_outcome="YES" if actual_outcome_value == 1.0 else "NO",
        sample_eligibility="ELIGIBLE",
        sample_status="READY",
    )


def get_candidate_count(client: TestClient) -> int:
    payload = client.get("/api/history/candidates").json()
    if isinstance(payload, list):
        return len(payload)
    return len(payload.get("items") or payload.get("candidates") or [])


def prepare_market_memory_inputs(client: TestClient, market_id: str = "tokyo_weather_market") -> None:
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
    weather = client.post(
        "/api/weather/probability",
        json={
            "market_id": market_id,
            "question": "Will Tokyo high temperature exceed 30C on June 1?",
            "yes_price": 0.52,
            "no_price": 0.48,
            "liquidity": 1000,
            "spread": 0.03,
        },
    ).json()
    assert weather["status"] == "ok"
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
    sample = client.post("/api/calibration-memory/build-sample", json={"market_id": market_id}).json()
    assert sample["status"] == "ok"
    deb = client.post("/api/deb-shadow/build", json={"market_id": market_id}).json()
    assert deb["status"] == "ok"
    emos = client.post("/api/emos-shadow/build", json={"market_id": market_id}).json()
    assert emos["status"] == "ok"


def test_models_serialize() -> None:
    record = ShadowEngineEvaluationRecord(
        shadow_evaluation_id="see_test",
        market_id="m1",
        calibration_sample_id="cs_1",
        outcome_resolution_id="orr_1",
        primary_probability=0.60,
        deb_probability=0.61,
        emos_probability=0.58,
        actual_outcome_value=1.0,
        primary_brier_score=0.16,
        deb_brier_score=0.1521,
        emos_brier_score=0.1764,
        primary_absolute_error=0.40,
        deb_absolute_error=0.39,
        emos_absolute_error=0.42,
        best_engine=BestShadowEngine.DEB_SHADOW,
        evaluation_status=ShadowEngineEvaluationStatus.READY,
    )
    dumped = record.model_dump(mode="json")
    assert dumped["best_engine"] == "DEB_SHADOW"
    assert dumped["evaluation_status"] == "READY"


def test_tables_created(tmp_path) -> None:
    db_path = str(tmp_path / "shadow_eval.sqlite")
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('shadow_engine_evaluations')"
            ).fetchall()
        }
    assert "shadow_engine_evaluations" in tables


def test_repository_save_list_query_summary(tmp_path) -> None:
    db_path = str(tmp_path / "repo.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    record = ShadowEngineEvaluationRecord(
        shadow_evaluation_id="see_repo",
        market_id="m1",
        calibration_sample_id="cs_1",
        outcome_resolution_id="orr_1",
        primary_probability=0.60,
        deb_probability=0.61,
        emos_probability=0.58,
        actual_outcome_value=1.0,
        primary_brier_score=0.16,
        deb_brier_score=0.1521,
        emos_brier_score=0.1764,
        primary_absolute_error=0.40,
        deb_absolute_error=0.39,
        emos_absolute_error=0.42,
        best_engine=BestShadowEngine.DEB_SHADOW,
        evaluation_status=ShadowEngineEvaluationStatus.READY,
    )
    repo.save_shadow_engine_evaluation(record)
    assert len(repo.list_shadow_engine_evaluations()) == 1
    assert repo.get_shadow_engine_evaluation_by_id("see_repo") is not None
    assert repo.get_latest_shadow_engine_evaluation_for_market("m1") is not None
    bundle = repo.get_shadow_engine_evaluation_bundle("m1")
    assert len(bundle.evaluations) == 1
    summary = repo.get_shadow_engine_evaluation_summary()
    assert summary.total_evaluations == 1
    assert summary.by_status["READY"] == 1
    assert summary.by_best_engine["DEB_SHADOW"] == 1


def test_service_build_for_market_from_accepted_memory(tmp_path) -> None:
    db_path = str(tmp_path / "service.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    repo.save_calibration_sample(
        make_sample(
            calibration_sample_id="cs_1",
            market_id="m1",
            market_probability=0.52,
            model_probability=0.60,
            actual_outcome_value=1.0,
        )
    )
    repo.save_calibration_sample(
        make_sample(
            calibration_sample_id="cs_2",
            market_id="m2",
            market_probability=0.45,
            model_probability=0.20,
            actual_outcome_value=0.0,
        )
    )
    DebShadowService(repo).build_for_market("m1")
    EmosShadowService(repo).build_for_market("m1")

    record = ShadowEngineEvaluationService(repo).build_for_market("m1")
    assert record.evaluation_status == ShadowEngineEvaluationStatus.READY
    assert record.primary_probability == 0.60
    assert record.deb_probability is not None
    assert record.emos_probability is not None
    assert record.primary_brier_score == (0.60 - 1.0) ** 2
    assert record.best_engine in {
        BestShadowEngine.GAUSSIAN,
        BestShadowEngine.DEB_SHADOW,
        BestShadowEngine.EMOS_SHADOW,
        BestShadowEngine.TIE,
    }


def test_shadow_evaluation_apis_do_not_create_candidates_or_trigger_promotion(tmp_path) -> None:
    client = make_client(tmp_path)
    prepare_market_memory_inputs(client, market_id="m_api")
    before_candidates = get_candidate_count(client)
    before_primary = client.get("/api/probability/engines").json()["primary"]["engine_id"]

    build = client.post("/api/shadow-evaluation/build", json={"market_id": "m_api"}).json()
    summary = client.get("/api/shadow-evaluation/summary").json()
    rows = client.get("/api/shadow-evaluation/evaluations").json()
    bundle = client.get("/api/shadow-evaluation/market/m_api").json()

    after_candidates = get_candidate_count(client)
    after_primary = client.get("/api/probability/engines").json()["primary"]["engine_id"]

    assert build["status"] == "ok"
    assert summary["status"] == "ok"
    assert rows["status"] == "ok"
    assert bundle["status"] == "ok"
    assert bundle["market_id"] == "m_api"
    assert after_candidates == before_candidates
    assert after_primary == before_primary
    assert build["safety"]["probability_engine_called"] is False
    assert build["safety"]["strategy_runner_called"] is False
    assert build["safety"]["candidates_created"] is False
    assert build["safety"]["simulation_triggered"] is False
    assert build["safety"]["execution_triggered"] is False
    assert build["safety"]["promotion_triggered"] is False
    assert build["safety"]["active_engine_changed"] is False


def test_build_all_and_live_execute_rejected(tmp_path) -> None:
    client = make_client(tmp_path)
    prepare_market_memory_inputs(client, market_id="m_all_1")
    prepare_market_memory_inputs(client, market_id="m_all_2")

    build_all = client.post("/api/shadow-evaluation/build-all", json={}).json()
    assert build_all["status"] == "ok"
    assert build_all["built_count"] >= 2
    assert build_all["safety"]["execution_triggered"] is False
    assert build_all["safety"]["promotion_triggered"] is False

    response = client.post("/api/settings/mode", json={"mode": "LIVE_EXECUTE"})
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "error"
    assert "LIVE_EXECUTE" in data["message"]
