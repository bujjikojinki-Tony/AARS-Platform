from __future__ import annotations

import sqlite3

from fastapi.testclient import TestClient

from backend.app_factory import create_app
from backend.models.outcome import MarketOutcomeRecord
from backend.models.outcome import MarketOutcomeSource
from backend.models.outcome import OutcomeDirection
from backend.models.outcome import OutcomeMetric
from backend.models.outcome import OutcomeResolutionRecord
from backend.models.outcome import OutcomeUnit
from backend.models.outcome import ResolvedOutcome
from backend.models.outcome import ResolutionStatus
from backend.models.outcome import WeatherActualRecord
from backend.models.outcome import WeatherActualSource
from backend.outcome.outcome_resolver_read_only_service import OutcomeResolverReadOnlyService
from backend.storage.db import init_db
from backend.storage.repositories import Repository


def make_client(tmp_path) -> TestClient:
    app = create_app(
        db_path=str(tmp_path / "pwb04g.sqlite"),
        allow_network=False,
        allow_polymarket_network=False,
        market_source_mode="MOCK_ONLY",
        archive_weather_on_probability_build=False,
    )
    return TestClient(app)


def make_probability_build(client: TestClient, market_id: str = "tokyo_weather_market") -> None:
    payload = {
        "market_id": market_id,
        "question": "Will Tokyo high temperature exceed 30C on June 1?",
        "yes_price": 0.52,
        "no_price": 0.48,
        "liquidity": 1000,
        "spread": 0.03,
    }
    response = client.post("/api/weather/probability", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def get_candidate_count(client: TestClient) -> int:
    payload = client.get("/api/history/candidates").json()
    if isinstance(payload, list):
        return len(payload)
    return len(payload.get("items") or payload.get("candidates") or [])


def test_outcome_models_serialize():
    market = MarketOutcomeRecord(
        market_outcome_id="mor_1",
        market_id="m1",
        source=MarketOutcomeSource.MANUAL,
        resolved_outcome=ResolvedOutcome.YES,
        resolution_status=ResolutionStatus.RESOLVED,
    )
    actual = WeatherActualRecord(
        weather_actual_id="war_1",
        market_id="m1",
        source=WeatherActualSource.MANUAL,
        metric=OutcomeMetric.TEMPERATURE_HIGH,
        unit=OutcomeUnit.C,
        actual_value=31.2,
    )
    resolution = OutcomeResolutionRecord(
        outcome_resolution_id="orr_1",
        market_id="m1",
        weather_actual_id="war_1",
        direction=OutcomeDirection.ABOVE,
        actual_value=31.2,
        threshold=30.0,
        resolved_outcome=ResolvedOutcome.YES,
        resolution_status=ResolutionStatus.RESOLVED,
        resolution_source=MarketOutcomeSource.WEATHER_ACTUAL,
    )
    assert market.model_dump(mode="json")["resolved_outcome"] == "YES"
    assert actual.model_dump(mode="json")["metric"] == "temperature_high"
    assert resolution.model_dump(mode="json")["direction"] == "ABOVE"


def test_outcome_tables_created(tmp_path):
    db_path = str(tmp_path / "outcomes.sqlite")
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('market_outcome_records','weather_actual_records','outcome_resolution_records')"
            ).fetchall()
        }
    assert "market_outcome_records" in tables
    assert "weather_actual_records" in tables
    assert "outcome_resolution_records" in tables


def test_repository_save_list_bundle_summary(tmp_path):
    db_path = str(tmp_path / "repo.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    service = OutcomeResolverReadOnlyService(repo)
    market = service.save_market_outcome(
        market_id="m1",
        resolved_outcome="YES",
        resolution_status="RESOLVED",
        resolved_value=31.2,
    )
    actual = service.save_weather_actual(
        market_id="m1",
        source="MANUAL",
        metric="temperature_high",
        unit="C",
        actual_value=31.2,
    )
    resolution = service.resolve_from_weather_actual(
        market_id="m1",
        weather_actual_id=actual.weather_actual_id,
        threshold=30.0,
        direction="ABOVE",
    )
    assert market.market_outcome_id.startswith("mor_")
    assert actual.weather_actual_id.startswith("war_")
    assert resolution.outcome_resolution_id.startswith("orr_")
    assert len(repo.list_market_outcome_records()) == 1
    assert len(repo.list_weather_actual_records()) == 1
    assert len(repo.list_outcome_resolution_records()) == 1
    assert repo.get_weather_actual_record_by_id(actual.weather_actual_id) is not None
    bundle = repo.get_outcome_bundle("m1")
    assert bundle.market_id == "m1"
    assert len(bundle.markets) == 1
    assert len(bundle.weather_actuals) == 1
    assert len(bundle.resolutions) == 1
    summary = repo.get_outcome_archive_summary()
    assert summary.market_outcome_records == 1
    assert summary.weather_actual_records == 1
    assert summary.outcome_resolution_records == 1
    assert summary.unique_markets == 1
    assert summary.by_resolution_status["RESOLVED"] == 1
    assert summary.by_resolved_outcome["YES"] == 1


def test_api_shapes_and_market_bundle(tmp_path):
    client = make_client(tmp_path)
    make_probability_build(client)
    market = client.post(
        "/api/outcomes/market",
        json={
            "market_id": "tokyo_weather_market",
            "resolved_outcome": "YES",
            "resolution_status": "RESOLVED",
            "resolved_value": 31.2,
        },
    ).json()
    actual = client.post(
        "/api/outcomes/weather-actual",
        json={
            "market_id": "tokyo_weather_market",
            "city": "Tokyo",
            "target_date": "2026-06-01",
            "source": "MANUAL",
            "metric": "temperature_high",
            "unit": "C",
            "actual_value": 31.2,
        },
    ).json()
    resolution = client.post(
        "/api/outcomes/resolve-from-weather",
        json={
            "market_id": "tokyo_weather_market",
            "weather_actual_id": actual["record"]["weather_actual_id"],
        },
    ).json()
    assert market["status"] == "ok"
    assert actual["status"] == "ok"
    assert resolution["status"] == "ok"
    assert client.get("/api/outcomes/summary").json()["status"] == "ok"
    assert client.get("/api/outcomes/markets").json()["status"] == "ok"
    assert client.get("/api/outcomes/weather-actuals").json()["status"] == "ok"
    assert client.get("/api/outcomes/resolutions").json()["status"] == "ok"
    bundle = client.get("/api/outcomes/market/tokyo_weather_market").json()
    assert bundle["status"] == "ok"
    assert bundle["market_id"] == "tokyo_weather_market"
    assert len(bundle["bundle"]["weather_actuals"]) == 1


def test_above_below_resolution_rules_and_missing_actual(tmp_path):
    client = make_client(tmp_path)
    make_probability_build(client, market_id="m_above")
    above_actual = client.post(
        "/api/outcomes/weather-actual",
        json={
            "market_id": "m_above",
            "source": "MANUAL",
            "metric": "temperature_high",
            "unit": "C",
            "actual_value": 31.2,
        },
    ).json()
    above = client.post(
        "/api/outcomes/resolve-from-weather",
        json={"market_id": "m_above", "weather_actual_id": above_actual["record"]["weather_actual_id"]},
    ).json()
    assert above["record"]["resolved_outcome"] == "YES"
    assert above["record"]["resolution_status"] == "RESOLVED"

    missing_actual = client.post(
        "/api/outcomes/weather-actual",
        json={
            "market_id": "m_above",
            "source": "MANUAL",
            "metric": "temperature_high",
            "unit": "C",
            "actual_value": None,
        },
    ).json()
    missing = client.post(
        "/api/outcomes/resolve-from-weather",
        json={"market_id": "m_above", "weather_actual_id": missing_actual["record"]["weather_actual_id"]},
    ).json()
    assert missing["record"]["resolved_outcome"] == "INSUFFICIENT_EVIDENCE"
    assert missing["record"]["resolution_status"] == "INSUFFICIENT_EVIDENCE"

    below_actual = client.post(
        "/api/outcomes/weather-actual",
        json={
            "market_id": "m_below",
            "source": "MANUAL",
            "metric": "temperature_high",
            "unit": "C",
            "actual_value": 25.0,
        },
    ).json()
    below = client.post(
        "/api/outcomes/resolve-from-weather",
        json={
            "market_id": "m_below",
            "weather_actual_id": below_actual["record"]["weather_actual_id"],
            "threshold": 30.0,
            "direction": "BELOW",
        },
    ).json()
    assert below["record"]["resolved_outcome"] == "YES"
    assert below["record"]["resolution_status"] == "RESOLVED"


def test_outcome_writes_do_not_create_candidates_or_trigger_execution_chain(tmp_path):
    client = make_client(tmp_path)
    before = get_candidate_count(client)
    market = client.post(
        "/api/outcomes/market",
        json={"market_id": "m1", "resolved_outcome": "UNKNOWN", "resolution_status": "PENDING"},
    ).json()
    actual = client.post(
        "/api/outcomes/weather-actual",
        json={
            "market_id": "m1",
            "source": "MANUAL",
            "metric": "temperature_high",
            "unit": "C",
            "actual_value": 30.1,
        },
    ).json()
    resolution = client.post(
        "/api/outcomes/resolve-from-weather",
        json={
            "market_id": "m1",
            "weather_actual_id": actual["record"]["weather_actual_id"],
            "threshold": 30.0,
            "direction": "ABOVE",
        },
    ).json()
    after = get_candidate_count(client)
    assert market["status"] == "ok"
    assert actual["status"] == "ok"
    assert resolution["status"] == "ok"
    assert after == before
    assert market["safety"]["simulation_triggered"] is False
    assert market["safety"]["execution_triggered"] is False
    assert market["safety"]["calibration_triggered"] is False
    assert market["safety"]["promotion_triggered"] is False
    assert resolution["safety"]["simulation_triggered"] is False
    assert resolution["safety"]["execution_triggered"] is False


def test_live_execute_still_rejected(tmp_path):
    client = make_client(tmp_path)
    client.post(
        "/api/outcomes/market",
        json={"market_id": "m1", "resolved_outcome": "UNKNOWN", "resolution_status": "PENDING"},
    )
    response = client.post("/api/settings/mode", json={"mode": "LIVE_EXECUTE"})
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "error"
    assert "LIVE_EXECUTE" in data["message"]
