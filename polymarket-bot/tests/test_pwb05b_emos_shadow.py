from __future__ import annotations

import sqlite3

from fastapi.testclient import TestClient

from backend.app_factory import create_app
from backend.emos_shadow.emos_shadow_service import EmosShadowService
from backend.models.calibration_memory import CalibrationSample
from backend.models.emos_shadow import EmosShadowDiagnosticRecord
from backend.models.emos_shadow import EmosShadowRunRecord
from backend.models.emos_shadow import EmosShadowRunStatus
from backend.storage.db import init_db
from backend.storage.repositories import Repository


def make_client(tmp_path) -> TestClient:
    app = create_app(
        db_path=str(tmp_path / "pwb05b.sqlite"),
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


def test_models_serialize() -> None:
    run = EmosShadowRunRecord(
        emos_shadow_run_id="esr_test",
        market_id="m1",
        calibration_sample_id="cs_1",
        engine_id="emos_shadow_v1",
        base_probability=0.6,
        emos_probability=0.612,
        location_adjustment=0.01,
        scale_adjustment=0.002,
        sample_count=3,
        run_status=EmosShadowRunStatus.READY,
        warnings=["shadow-only"],
    )
    diagnostic = EmosShadowDiagnosticRecord(
        emos_shadow_diagnostic_id="esd_test",
        emos_shadow_run_id="esr_test",
        market_id="m1",
        sample_count=3,
        avg_model_brier_score=0.12,
        avg_market_brier_score=0.18,
        avg_probability_error=0.03,
        avg_absolute_error=0.11,
        location_weight=0.12,
        scale_weight=0.11,
        notes="diagnostic",
    )

    assert run.model_dump(mode="json")["run_status"] == "READY"
    assert diagnostic.model_dump(mode="json")["sample_count"] == 3


def test_tables_created(tmp_path) -> None:
    db_path = str(tmp_path / "emos_shadow.sqlite")
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('emos_shadow_runs','emos_shadow_diagnostics')"
            ).fetchall()
        }
    assert "emos_shadow_runs" in tables
    assert "emos_shadow_diagnostics" in tables


def test_repository_save_list_query_summary(tmp_path) -> None:
    db_path = str(tmp_path / "repo.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    run = EmosShadowRunRecord(
        emos_shadow_run_id="esr_repo",
        market_id="m1",
        calibration_sample_id="cs_1",
        base_probability=0.55,
        emos_probability=0.561,
        location_adjustment=0.01,
        scale_adjustment=0.001,
        sample_count=4,
        run_status=EmosShadowRunStatus.READY,
        warnings=["shadow-only"],
    )
    diagnostic = EmosShadowDiagnosticRecord(
        emos_shadow_diagnostic_id="esd_repo",
        emos_shadow_run_id="esr_repo",
        market_id="m1",
        calibration_sample_id="cs_1",
        sample_count=4,
        avg_model_brier_score=0.11,
        avg_market_brier_score=0.14,
        avg_probability_error=0.02,
        avg_absolute_error=0.08,
        location_weight=0.16,
        scale_weight=0.08,
        notes="repo-test",
    )
    repo.save_emos_shadow_run(run)
    repo.save_emos_shadow_diagnostic(diagnostic)

    assert len(repo.list_emos_shadow_runs()) == 1
    assert len(repo.list_emos_shadow_diagnostics()) == 1
    assert repo.get_emos_shadow_run_by_id("esr_repo") is not None
    assert repo.get_latest_emos_shadow_run_for_market("m1") is not None
    bundle = repo.get_emos_shadow_market_bundle("m1")
    assert len(bundle.runs) == 1
    assert len(bundle.diagnostics) == 1
    summary = repo.get_emos_shadow_summary()
    assert summary.total_runs == 1
    assert summary.total_diagnostics == 1
    assert summary.by_run_status["READY"] == 1


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

    result = EmosShadowService(repo).build_for_market("m1")
    run = result["run"]
    diagnostic = result["diagnostic"]

    assert run.run_status == EmosShadowRunStatus.READY
    assert run.sample_count == 2
    assert run.base_probability == 0.60
    assert round(float(run.location_adjustment or 0.0), 6) == 0.004
    assert round(float(run.scale_adjustment or 0.0), 6) == 0.00048
    assert round(float(run.emos_probability or 0.0), 6) == 0.60448
    assert diagnostic.sample_count == 2
    assert any("shadow-only" in warning for warning in run.warnings)


def test_emos_shadow_apis_do_not_create_candidates_or_change_primary_engine(tmp_path) -> None:
    client = make_client(tmp_path)
    prepare_market_memory_inputs(client, market_id="m_api")
    before_candidates = get_candidate_count(client)
    before_primary = client.get("/api/probability/engines").json()["primary"]["engine_id"]

    build = client.post("/api/emos-shadow/build", json={"market_id": "m_api"}).json()
    summary = client.get("/api/emos-shadow/summary").json()
    runs = client.get("/api/emos-shadow/runs").json()
    diagnostics = client.get("/api/emos-shadow/diagnostics").json()
    bundle = client.get("/api/emos-shadow/market/m_api").json()

    after_candidates = get_candidate_count(client)
    after_primary = client.get("/api/probability/engines").json()["primary"]["engine_id"]

    assert build["status"] == "ok"
    assert summary["status"] == "ok"
    assert runs["status"] == "ok"
    assert diagnostics["status"] == "ok"
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


def test_build_all_eligible_and_live_execute_rejected(tmp_path) -> None:
    client = make_client(tmp_path)
    prepare_market_memory_inputs(client, market_id="m_all_1")
    prepare_market_memory_inputs(client, market_id="m_all_2")

    build_all = client.post("/api/emos-shadow/build-all", json={}).json()
    assert build_all["status"] == "ok"
    assert build_all["built_count"] >= 2
    assert build_all["safety"]["execution_triggered"] is False
    assert build_all["safety"]["promotion_triggered"] is False

    response = client.post("/api/settings/mode", json={"mode": "LIVE_EXECUTE"})
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "error"
    assert "LIVE_EXECUTE" in data["message"]
