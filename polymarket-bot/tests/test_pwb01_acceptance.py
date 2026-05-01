from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.routes_command import create_command_router
from backend.api.routes_history import create_history_router
from backend.api.routes_opportunities import create_opportunities_router
from backend.api.routes_settings import create_settings_router
from backend.execution.risk_manager import RiskManager
from backend.execution.simulator import Simulator
from backend.execution.strategy_runner import StrategyRunner
from backend.governance.rule_registry import RuleRegistry
from backend.models.core import OpportunityCandidate
from backend.models.enums import Side
from backend.probability.placeholder_probability_provider import PlaceholderProbabilityProvider
from backend.sources.mock_market_source import MockMarketSource
from backend.storage.db import init_db
from backend.storage.repositories import Repository
from backend.strategies.binary_arb_strategy import BinaryArbStrategy
from backend.strategies.weather_edge_strategy import WeatherEdgeStrategy


def _build_test_client(db_path: str) -> tuple[TestClient, Repository]:
    init_db(db_path)
    repository = Repository(db_path)
    probability_provider = PlaceholderProbabilityProvider()
    market_source = MockMarketSource()
    risk_manager = RiskManager()
    strategy_runner = StrategyRunner(
        market_source=market_source,
        strategies=[
            WeatherEdgeStrategy(probability_provider),
            BinaryArbStrategy(),
        ],
        risk_manager=risk_manager,
        repository=repository,
    )
    simulator = Simulator(repository)
    rule_registry = RuleRegistry(repository)

    app = FastAPI(title="PWB-01 Acceptance Test App")

    @app.get("/healthz")
    def healthz():
        return {
            "status": "ok",
            "mode": repository.get_mode(),
            "live_execution": False,
        }

    app.include_router(create_opportunities_router(repository, strategy_runner))
    app.include_router(create_command_router(repository, strategy_runner, simulator, rule_registry))
    app.include_router(create_history_router(repository))
    app.include_router(create_settings_router(rule_registry))
    return TestClient(app), repository


def test_scan_creates_candidate(tmp_path) -> None:
    client, repository = _build_test_client(str(tmp_path / "acceptance_scan.sqlite"))

    response = client.post("/api/opportunities/scan")
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["candidates_count"] >= 1
    assert len(repository.list_table("market_snapshots")) >= 5
    assert len(repository.list_table("strategy_signals")) >= 1
    assert len(repository.list_table("opportunity_candidates")) >= 1
    assert any(item["event_type"] == "CANDIDATE_CREATED" for item in repository.list_table("audit_logs"))


def test_risk_gate_blocks_weak_candidate() -> None:
    risk_manager = RiskManager()
    candidate = OpportunityCandidate(
        candidate_id="cand_weak",
        signal_id="sig_weak",
        market_id="mock_weather_weak_edge",
        question="Weak edge candidate",
        side=Side.YES,
        market_probability=0.50,
        model_probability=0.51,
        edge_percent=1.0,
        liquidity=1000,
        spread=0.03,
    )

    result = risk_manager.evaluate(candidate)

    assert result.status.value == "BLOCK"
    assert "edge below threshold" in result.reasons


def test_simulation_does_not_trade_live(tmp_path) -> None:
    client, repository = _build_test_client(str(tmp_path / "acceptance_sim.sqlite"))

    scan_response = client.post("/api/opportunities/scan")
    candidates = scan_response.json()["candidates"]
    candidate = next(item for item in candidates if item["action_status"] == "SIMULATE")

    response = client.post("/api/command", json={"command": f"/simulate {candidate['candidate_id']}"})
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["simulation"]["result_status"] == "COMPLETED"
    assert repository.get_mode() != "LIVE_EXECUTE"
    audit_rows = repository.list_table("audit_logs")
    simulation_audit = next(item for item in audit_rows if item["event_type"] == "SIMULATION_CREATED")
    assert simulation_audit["payload"]["live_execution"] is False


def test_mode_defaults_to_observe_only(tmp_path) -> None:
    client, _repository = _build_test_client(str(tmp_path / "acceptance_mode.sqlite"))

    response = client.get("/api/settings/mode")
    payload = response.json()

    assert response.status_code == 200
    assert payload["mode"] == "OBSERVE_ONLY"


def test_command_is_audited(tmp_path) -> None:
    client, repository = _build_test_client(str(tmp_path / "acceptance_audit.sqlite"))

    response = client.post("/api/command", json={"command": "/run scan"})
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "ok"
    audit_rows = repository.list_table("audit_logs")
    command_audit = next(item for item in audit_rows if item["event_type"] == "COMMAND_EXECUTED")
    assert command_audit["payload"]["command"] == "/run scan"
