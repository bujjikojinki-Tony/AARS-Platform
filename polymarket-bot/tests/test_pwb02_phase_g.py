from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.routes_evidence import create_evidence_router
from backend.api.routes_opportunities import create_opportunities_router
from backend.api.routes_settings import create_settings_router
from backend.api.routes_weather import create_weather_router
from backend.api.routes_workstation import create_workstation_router
from backend.execution.risk_manager import RiskManager
from backend.execution.simulator import Simulator
from backend.execution.strategy_runner import StrategyRunner
from backend.governance.rule_registry import RuleRegistry
from backend.probability.weather_probability_provider import WeatherProbabilityProvider
from backend.sources.mock_market_source import MockMarketSource
from backend.storage.db import init_db
from backend.storage.repositories import Repository
from backend.strategies.binary_arb_strategy import BinaryArbStrategy
from backend.strategies.weather_edge_strategy import WeatherEdgeStrategy


def _build_test_client(db_path: str) -> tuple[TestClient, Repository]:
    init_db(db_path)
    repository = Repository(db_path)
    probability_provider = WeatherProbabilityProvider(
        repository=repository,
        default_year=2026,
        allow_network=False,
        default_sigma=2.5,
    )
    strategy_runner = StrategyRunner(
        market_source=MockMarketSource(),
        strategies=[
            WeatherEdgeStrategy(probability_provider),
            BinaryArbStrategy(),
        ],
        risk_manager=RiskManager(),
        repository=repository,
    )
    simulator = Simulator(repository)
    rule_registry = RuleRegistry(repository)

    app = FastAPI(title="PWB-02 Phase G Test App")
    app.include_router(create_opportunities_router(repository, strategy_runner))
    app.include_router(create_weather_router(repository, default_year=2026, allow_network=False))
    app.include_router(create_evidence_router(repository))
    app.include_router(create_workstation_router(repository))
    app.include_router(create_settings_router(rule_registry))
    return TestClient(app), repository


def test_weather_and_workstation_apis(tmp_path) -> None:
    client, repository = _build_test_client(str(tmp_path / "phase_g.sqlite"))

    resolve_response = client.post(
        "/api/weather/resolve",
        json={
            "market_id": "mock_weather_strong_yes",
            "question": "Will Tokyo high temperature exceed 30C on June 1?",
        },
    )
    assert resolve_response.status_code == 200
    resolve_payload = resolve_response.json()
    assert resolve_payload["status"] == "ok"
    assert resolve_payload["descriptor"]["city"] == "Tokyo"
    assert resolve_payload["descriptor"]["threshold"] == 30.0

    probability_response = client.post(
        "/api/weather/probability",
        json={
            "market_id": "mock_weather_strong_yes",
            "question": "Will Tokyo high temperature exceed 30C on June 1?",
            "yes_price": 0.52,
            "no_price": 0.49,
            "liquidity": 1000,
            "spread": 0.03,
        },
    )
    assert probability_response.status_code == 200
    probability_payload = probability_response.json()
    assert probability_payload["status"] == "ok"
    assert 0.67 < probability_payload["probability"]["model_probability"] < 0.70
    assert probability_payload["latest_weather_view"]["evidence_summary"]
    assert probability_payload["latest_evidence_pack"]["descriptor"]["city"] == "Tokyo"

    descriptor_response = client.get("/api/weather/descriptor/mock_weather_strong_yes")
    assert descriptor_response.status_code == 200
    assert descriptor_response.json()["descriptor"]["parse_warnings"] == []

    evidence_response = client.get("/api/weather/evidence/mock_weather_strong_yes")
    assert evidence_response.status_code == 200
    evidence_payload = evidence_response.json()
    assert evidence_payload["evidence_pack"]["raw_refs"]
    assert evidence_payload["sources"][0]["raw_payload"]["mock"] is True

    view_response = client.get("/api/weather/view/mock_weather_strong_yes")
    assert view_response.status_code == 200
    view_payload = view_response.json()
    assert view_payload["weather_view"]["invalidation_rules"]

    probability_get_response = client.get("/api/weather/probability/mock_weather_strong_yes")
    assert probability_get_response.status_code == 200
    probability_get_payload = probability_get_response.json()
    assert probability_get_payload["probability_view"]["warnings"] == []

    packs_response = client.get("/api/evidence/packs")
    assert packs_response.status_code == 200
    assert packs_response.json()["items"]

    workstation_response = client.get("/api/workstation/mock_weather_strong_yes")
    assert workstation_response.status_code == 200
    workstation_payload = workstation_response.json()
    assert workstation_payload["descriptor"]["city"] == "Tokyo"
    assert workstation_payload["evidence_pack"]["descriptor"]["city"] == "Tokyo"
    assert workstation_payload["probability_view"]["model_probability"] > 0.67

    assert repository.get_latest_weather_descriptor("mock_weather_strong_yes") is not None
