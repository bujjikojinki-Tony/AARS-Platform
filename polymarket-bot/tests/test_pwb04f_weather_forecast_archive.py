from __future__ import annotations

import sqlite3

from fastapi.testclient import TestClient

from backend.app_factory import create_app
from backend.archive.weather_forecast_archive_service import WeatherForecastArchiveService
from backend.models.weather import EvidenceConflictLevel
from backend.models.weather import EvidenceFreshness
from backend.models.weather import EvidencePack
from backend.models.weather import ParseConfidence
from backend.models.weather import SourceType
from backend.models.weather import WeatherDirection
from backend.models.weather import WeatherMarketDescriptor
from backend.models.weather import WeatherMetric
from backend.models.weather import WeatherSourceRecord
from backend.models.weather import WeatherUnit
from backend.models.weather import WeatherView
from backend.models.weather_archive import WeatherArchiveReason
from backend.storage.db import init_db
from backend.storage.repositories import Repository


def make_client(tmp_path, *, archive_weather_on_probability_build: bool = False) -> TestClient:
    app = create_app(
        db_path=str(tmp_path / f"pwb04f_{archive_weather_on_probability_build}.sqlite"),
        allow_network=False,
        allow_polymarket_network=False,
        market_source_mode="MOCK_ONLY",
        archive_weather_on_probability_build=archive_weather_on_probability_build,
    )
    return TestClient(app)


def make_descriptor(market_id: str = "weather_market_1") -> WeatherMarketDescriptor:
    return WeatherMarketDescriptor(
        market_id=market_id,
        question="Will Tokyo high temperature exceed 30C on June 1?",
        city="Tokyo",
        target_date="2026-06-01",
        metric=WeatherMetric.DAILY_HIGH,
        threshold=30.0,
        unit=WeatherUnit.C,
        direction=WeatherDirection.ABOVE,
        confidence=ParseConfidence.HIGH,
    )


def make_source(market_id: str = "weather_market_1") -> WeatherSourceRecord:
    return WeatherSourceRecord(
        source_id="openmeteo_tokyo",
        market_id=market_id,
        source_name="Open-Meteo",
        source_type=SourceType.FORECAST,
        city="Tokyo",
        target_date="2026-06-01",
        normalized_value=31.2,
        unit=WeatherUnit.C,
        raw_payload={"mock": True},
    )


def make_evidence_pack(market_id: str = "weather_market_1") -> EvidencePack:
    return EvidencePack(
        evidence_pack_id="ep_1",
        market_id=market_id,
        descriptor=make_descriptor(market_id),
        sources=[make_source(market_id)],
        evidence_freshness=EvidenceFreshness.FRESH,
        evidence_conflict_level=EvidenceConflictLevel.NONE,
        raw_refs=["mock://openmeteo_tokyo"],
    )


def make_weather_view(market_id: str = "weather_market_1") -> WeatherView:
    return WeatherView(
        weather_view_id="wv_1",
        evidence_pack_id="ep_1",
        market_id=market_id,
        city="Tokyo",
        target_date="2026-06-01",
        expected_value=31.2,
        expected_range_low=29.8,
        expected_range_high=32.6,
        sigma=1.4,
        threshold=30.0,
        direction=WeatherDirection.ABOVE,
        unit=WeatherUnit.C,
        confidence=ParseConfidence.HIGH,
        evidence_summary=["Open-Meteo indicates a high near 31C."],
        invalidation_rules=["A colder revision below 30C invalidates the edge."],
        confirmation_rules=["Persistent highs above 30C confirm the thesis."],
    )


def get_candidate_count(client: TestClient) -> int:
    payload = client.get("/api/history/candidates").json()
    if isinstance(payload, list):
        return len(payload)
    return len(payload.get("items") or payload.get("candidates") or [])


def test_weather_archive_tables_created(tmp_path):
    db_path = str(tmp_path / "weather_archive.sqlite")
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'weather_%_archive'"
            ).fetchall()
        }
    assert "weather_forecast_archive" in tables
    assert "weather_evidence_archive" in tables
    assert "weather_view_archive" in tables


def test_weather_archive_service_summary_and_bundle(tmp_path):
    db_path = str(tmp_path / "service.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    service = WeatherForecastArchiveService(repo)

    view = make_weather_view()
    evidence = make_evidence_pack()
    service.archive_weather_view(view, WeatherArchiveReason.MANUAL_CAPTURE)
    service.archive_evidence_pack(view.market_id, evidence, WeatherArchiveReason.MANUAL_CAPTURE)
    service.archive_forecast_record(
        market_id=view.market_id,
        weather_view_id=view.weather_view_id,
        evidence_pack_id=evidence.evidence_pack_id,
        source_id="openmeteo_tokyo",
        source_type="OPEN_METEO",
        metric="temperature_high",
        unit="C",
        expected_value=31.2,
        expected_range_low=29.8,
        expected_range_high=32.6,
        sigma=1.4,
        archive_reason="MANUAL_CAPTURE",
        city="Tokyo",
        target_date="2026-06-01",
    )

    summary = repo.get_weather_archive_summary()
    assert summary.forecast_records == 1
    assert summary.evidence_records == 1
    assert summary.weather_view_records == 1
    assert summary.unique_markets == 1
    assert summary.by_source_type["OPEN_METEO"] == 1
    assert summary.by_archive_reason["MANUAL_CAPTURE"] == 3

    bundle = repo.get_weather_archive_bundle(view.market_id)
    assert bundle.market_id == view.market_id
    assert len(bundle.forecasts) == 1
    assert len(bundle.evidence) == 1
    assert len(bundle.weather_views) == 1


def test_weather_archive_latest_api_does_not_create_candidates_or_fetch_weather(tmp_path):
    client = make_client(tmp_path)
    build = client.post(
        "/api/weather/probability",
        json={
            "market_id": "tokyo_weather_market",
            "question": "Will Tokyo high temperature exceed 30C on June 1?",
            "yes_price": 0.52,
            "no_price": 0.48,
            "liquidity": 1000,
            "spread": 0.03,
        },
    ).json()
    assert build["status"] == "ok"

    before_candidates = get_candidate_count(client)
    response = client.post("/api/weather-archive/latest/tokyo_weather_market")
    data = response.json()
    after_candidates = get_candidate_count(client)

    assert response.status_code == 200
    assert data["status"] == "ok"
    assert len(data["weather_views"]) == 1
    assert data["safety"]["weather_fetch_triggered"] is False
    assert data["safety"]["strategy_runner_called"] is False
    assert data["safety"]["simulation_triggered"] is False
    assert data["safety"]["execution_triggered"] is False
    assert before_candidates == after_candidates


def test_probability_build_archive_optional_works(tmp_path):
    client = make_client(tmp_path, archive_weather_on_probability_build=True)
    response = client.post(
        "/api/weather/probability",
        json={
            "market_id": "tokyo_weather_market",
            "question": "Will Tokyo high temperature exceed 30C on June 1?",
            "yes_price": 0.52,
            "no_price": 0.48,
            "liquidity": 1000,
            "spread": 0.03,
        },
    )
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "ok"

    summary = client.get("/api/weather-archive/summary").json()
    assert summary["status"] == "ok"
    assert summary["summary"]["weather_view_records"] >= 1
    assert summary["summary"]["evidence_records"] >= 1
    assert summary["summary"]["forecast_records"] >= 1
    assert summary["summary"]["by_archive_reason"]["PROBABILITY_BUILD_CAPTURE"] >= 3


def test_scan_candidate_count_unchanged_with_weather_archive_flag(tmp_path):
    client_without = make_client(tmp_path / "without", archive_weather_on_probability_build=False)
    client_with = make_client(tmp_path / "with", archive_weather_on_probability_build=True)

    scan_without = client_without.post("/api/opportunities/scan").json()
    scan_with = client_with.post("/api/opportunities/scan").json()

    assert scan_without["status"] == "ok"
    assert scan_with["status"] == "ok"
    assert scan_without["candidates_count"] == scan_with["candidates_count"]


def test_weather_archive_read_api_shapes(tmp_path):
    client = make_client(tmp_path, archive_weather_on_probability_build=True)
    client.post(
        "/api/weather/probability",
        json={
            "market_id": "tokyo_weather_market",
            "question": "Will Tokyo high temperature exceed 30C on June 1?",
        },
    )
    assert client.get("/api/weather-archive/summary").json()["status"] == "ok"
    assert client.get("/api/weather-archive/views").json()["status"] == "ok"
    assert client.get("/api/weather-archive/forecasts").json()["status"] == "ok"
    assert client.get("/api/weather-archive/evidence").json()["status"] == "ok"
    bundle = client.get("/api/weather-archive/market/tokyo_weather_market").json()
    assert bundle["status"] == "ok"
    assert bundle["market_id"] == "tokyo_weather_market"


def test_live_execute_still_rejected(tmp_path):
    client = make_client(tmp_path, archive_weather_on_probability_build=True)
    client.post(
        "/api/weather/probability",
        json={
            "market_id": "tokyo_weather_market",
            "question": "Will Tokyo high temperature exceed 30C on June 1?",
        },
    )
    client.post("/api/weather-archive/latest/tokyo_weather_market")
    response = client.post("/api/settings/mode", json={"mode": "LIVE_EXECUTE"})
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "error"
    assert "LIVE_EXECUTE" in data["message"]
