from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.execution.risk_manager import RiskManager
from backend.execution.strategy_runner import StrategyRunner
from backend.app_factory import create_app
from backend.models.core import MarketSnapshot
from backend.models.weather import EvidenceConflictLevel
from backend.models.weather import EvidenceFreshness
from backend.models.weather import FreshnessStatus
from backend.models.weather import SourceType
from backend.models.weather import TrustLevel
from backend.models.weather import WeatherDirection
from backend.models.weather import WeatherMetric
from backend.models.weather import WeatherUnit
from backend.probability.gaussian_probability_engine import GaussianProbabilityEngine
from backend.probability.probability_view_builder import ProbabilityViewBuilder
from backend.probability.weather_probability_provider import WeatherProbabilityProvider
from backend.sources.mock_market_source import MockMarketSource
from backend.storage.db import init_db
from backend.storage.repositories import Repository
from backend.strategies.weather_edge_strategy import WeatherEdgeStrategy
from backend.weather.evidence_pack_builder import EvidencePackBuilder
from backend.weather.market_question_parser import MarketQuestionParser
from backend.weather.noaa_source import NoaaPlaceholderSource
from backend.weather.open_meteo_source import OpenMeteoSource
from backend.weather.source_health_checker import SourceHealthChecker
from backend.weather.weather_market_resolver import WeatherMarketResolver
from backend.weather.weather_source_registry import WeatherSourceRegistry
from backend.weather.weather_view_builder import WeatherViewBuilder


@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / "pwb02_test.sqlite"
    init_db(str(db_path))
    return str(db_path)


@pytest.fixture
def repository(test_db):
    return Repository(test_db)


@pytest.fixture
def app(test_db):
    return create_app(test_db, allow_network=False)


@pytest.fixture
def client(app):
    return TestClient(app)


def test_market_question_parser_parses_tokyo_high_temperature():
    parser = MarketQuestionParser(default_year=2026)
    descriptor = parser.parse(
        market_id="mock_weather_strong_yes",
        question="Will Tokyo high temperature exceed 30C on June 1?",
    )
    assert descriptor.market_id == "mock_weather_strong_yes"
    assert descriptor.city == "Tokyo"
    assert descriptor.country is None
    assert descriptor.target_date == "2026-06-01"
    assert descriptor.metric == WeatherMetric.DAILY_HIGH
    assert descriptor.threshold == 30
    assert descriptor.unit == WeatherUnit.C
    assert descriptor.direction == WeatherDirection.ABOVE
    assert descriptor.confidence.value in {"MEDIUM", "HIGH"}


def test_market_question_parser_parses_nyc_fahrenheit():
    parser = MarketQuestionParser(default_year=2026)
    descriptor = parser.parse(
        market_id="mock_weather_nyc",
        question="Will NYC daily high be above 85F on July 4, 2026?",
    )
    assert descriptor.city == "New York"
    assert descriptor.region == "NY"
    assert descriptor.country is None
    assert descriptor.target_date == "2026-07-04"
    assert descriptor.metric == WeatherMetric.DAILY_HIGH
    assert descriptor.threshold == 85
    assert descriptor.unit == WeatherUnit.F
    assert descriptor.direction == WeatherDirection.ABOVE


def test_weather_market_resolver_defaults_temperature_unit():
    parser = MarketQuestionParser(default_year=2026)
    resolver = WeatherMarketResolver()
    descriptor = parser.parse(
        market_id="mock_weather_missing_unit",
        question="Will Tokyo high temperature exceed 30 on June 1?",
    )
    resolved = resolver.resolve(descriptor)
    assert resolved.city == "Tokyo"
    assert resolved.metric == WeatherMetric.DAILY_HIGH
    assert resolved.unit == WeatherUnit.C
    assert "unit defaulted to C for temperature metric" in resolved.parse_warnings


def test_open_meteo_source_mock_fetch():
    parser = MarketQuestionParser(default_year=2026)
    resolver = WeatherMarketResolver()
    descriptor = resolver.resolve(
        parser.parse(
            market_id="mock_weather_strong_yes",
            question="Will Tokyo high temperature exceed 30C on June 1?",
        )
    )
    source = OpenMeteoSource(allow_network=False)
    assert source.supports(descriptor)
    record = source.fetch(descriptor)
    assert record.market_id == "mock_weather_strong_yes"
    assert record.source_name == "open_meteo_mock"
    assert record.source_type == SourceType.FORECAST
    assert record.city == "Tokyo"
    assert record.target_date == "2026-06-01"
    assert record.normalized_value == 31.2
    assert record.unit == WeatherUnit.C
    assert record.trust_level == TrustLevel.PRIMARY
    assert record.raw_payload["mock"] is True


def test_noaa_placeholder_only_supports_us():
    parser = MarketQuestionParser(default_year=2026)
    resolver = WeatherMarketResolver()
    noaa = NoaaPlaceholderSource()
    tokyo = resolver.resolve(
        parser.parse(
            market_id="mock_tokyo",
            question="Will Tokyo high temperature exceed 30C on June 1?",
        )
    )
    nyc = resolver.resolve(
        parser.parse(
            market_id="mock_nyc",
            question="Will NYC daily high be above 85F on July 4, 2026?",
        )
    )
    assert noaa.supports(tokyo) is False
    assert noaa.supports(nyc) is True
    record = noaa.fetch(nyc)
    assert record.source_name == "noaa_placeholder"
    assert record.source_type == SourceType.SHADOW
    assert record.trust_level == TrustLevel.SHADOW
    assert record.raw_payload["mock"] is True


def test_source_registry_selects_sources():
    parser = MarketQuestionParser(default_year=2026)
    resolver = WeatherMarketResolver()
    descriptor = resolver.resolve(
        parser.parse(
            market_id="mock_weather_strong_yes",
            question="Will Tokyo high temperature exceed 30C on June 1?",
        )
    )
    registry = WeatherSourceRegistry(
        sources=[
            OpenMeteoSource(allow_network=False),
            NoaaPlaceholderSource(),
        ]
    )
    selected = registry.select_sources(descriptor)
    assert len(selected) == 1
    assert selected[0].source_name == "open_meteo"


def test_source_health_checker_marks_fresh():
    parser = MarketQuestionParser(default_year=2026)
    resolver = WeatherMarketResolver()
    checker = SourceHealthChecker()
    descriptor = resolver.resolve(
        parser.parse(
            market_id="mock_weather_strong_yes",
            question="Will Tokyo high temperature exceed 30C on June 1?",
        )
    )
    record = OpenMeteoSource(allow_network=False).fetch(descriptor)
    checked = checker.check(record)
    assert checked.freshness_status == FreshnessStatus.FRESH


def test_evidence_pack_builder_builds_fresh_pack():
    parser = MarketQuestionParser(default_year=2026)
    resolver = WeatherMarketResolver()
    checker = SourceHealthChecker()
    descriptor = resolver.resolve(
        parser.parse(
            market_id="mock_weather_strong_yes",
            question="Will Tokyo high temperature exceed 30C on June 1?",
        )
    )
    record = checker.check(OpenMeteoSource(allow_network=False).fetch(descriptor))
    pack = EvidencePackBuilder().build(descriptor, [record])
    assert pack.market_id == "mock_weather_strong_yes"
    assert pack.descriptor.city == "Tokyo"
    assert len(pack.sources) == 1
    assert pack.evidence_freshness == EvidenceFreshness.FRESH
    assert pack.evidence_conflict_level == EvidenceConflictLevel.NONE
    assert record.source_id in pack.raw_refs


def test_weather_view_builder_builds_weather_view():
    parser = MarketQuestionParser(default_year=2026)
    resolver = WeatherMarketResolver()
    checker = SourceHealthChecker()
    descriptor = resolver.resolve(
        parser.parse(
            market_id="mock_weather_strong_yes",
            question="Will Tokyo high temperature exceed 30C on June 1?",
        )
    )
    record = checker.check(OpenMeteoSource(allow_network=False).fetch(descriptor))
    pack = EvidencePackBuilder().build(descriptor, [record])
    view = WeatherViewBuilder(default_sigma=2.5).build(pack)
    assert view.market_id == "mock_weather_strong_yes"
    assert view.city == "Tokyo"
    assert view.target_date == "2026-06-01"
    assert view.expected_value == 31.2
    assert view.expected_range_low == 28.7
    assert view.expected_range_high == 33.7
    assert view.sigma == 2.5
    assert view.threshold == 30
    assert view.direction == WeatherDirection.ABOVE
    assert len(view.evidence_summary) >= 1
    assert len(view.invalidation_rules) >= 1
    assert len(view.confirmation_rules) >= 1


def test_gaussian_probability_engine_above():
    parser = MarketQuestionParser(default_year=2026)
    resolver = WeatherMarketResolver()
    checker = SourceHealthChecker()
    descriptor = resolver.resolve(
        parser.parse(
            market_id="mock_weather_strong_yes",
            question="Will Tokyo high temperature exceed 30C on June 1?",
        )
    )
    record = checker.check(OpenMeteoSource(allow_network=False).fetch(descriptor))
    pack = EvidencePackBuilder().build(descriptor, [record])
    view = WeatherViewBuilder(default_sigma=2.5).build(pack)
    probability, warnings = GaussianProbabilityEngine().compute(view)
    assert 0.67 < probability < 0.70
    assert warnings == []


def test_probability_view_builder_outputs_probability_view():
    parser = MarketQuestionParser(default_year=2026)
    resolver = WeatherMarketResolver()
    checker = SourceHealthChecker()
    descriptor = resolver.resolve(
        parser.parse(
            market_id="mock_weather_strong_yes",
            question="Will Tokyo high temperature exceed 30C on June 1?",
        )
    )
    record = checker.check(OpenMeteoSource(allow_network=False).fetch(descriptor))
    pack = EvidencePackBuilder().build(descriptor, [record])
    view = WeatherViewBuilder(default_sigma=2.5).build(pack)
    probability_view = ProbabilityViewBuilder().build(view)
    assert probability_view.market_id == "mock_weather_strong_yes"
    assert probability_view.engine_id == "gaussian_v0"
    assert 0.67 < probability_view.model_probability < 0.70
    assert probability_view.threshold == 30
    assert probability_view.direction == WeatherDirection.ABOVE


def test_weather_probability_provider_persists_chain(repository):
    market = MarketSnapshot(
        market_id="mock_weather_strong_yes",
        question="Will Tokyo high temperature exceed 30C on June 1?",
        yes_price=0.52,
        no_price=0.49,
        liquidity=1000,
        spread=0.03,
    )
    provider = WeatherProbabilityProvider(
        repository=repository,
        default_year=2026,
        allow_network=False,
        default_sigma=2.5,
    )
    probability_view = provider.build_probability_view(market)
    assert 0.67 < probability_view.model_probability < 0.70
    assert repository.get_latest_weather_descriptor(market.market_id) is not None
    assert repository.get_latest_evidence_pack(market.market_id) is not None
    assert repository.get_latest_weather_view(market.market_id) is not None
    assert repository.get_latest_probability_view(market.market_id) is not None


def test_weather_edge_strategy_uses_weather_probability_provider(repository):
    market = MarketSnapshot(
        market_id="mock_weather_strong_yes",
        question="Will Tokyo high temperature exceed 30C on June 1?",
        yes_price=0.52,
        no_price=0.49,
        liquidity=1000,
        spread=0.03,
    )
    provider = WeatherProbabilityProvider(
        repository=repository,
        default_year=2026,
        allow_network=False,
        default_sigma=2.5,
    )
    strategy = WeatherEdgeStrategy(
        probability_provider=provider,
        min_edge_percent=10,
    )
    signal = strategy.evaluate(market)
    assert signal is not None
    assert signal.strategy_id == "weather_edge_v0"
    assert signal.side.value == "YES"
    assert 0.67 < signal.model_probability < 0.70
    assert signal.market_probability == 0.52
    assert signal.edge_percent > 10
    assert "Gaussian v0" in signal.reason


def test_strategy_runner_persists_weather_chain(repository):
    provider = WeatherProbabilityProvider(
        repository=repository,
        default_year=2026,
        allow_network=False,
        default_sigma=2.5,
    )
    runner = StrategyRunner(
        market_source=MockMarketSource(),
        strategies=[
            WeatherEdgeStrategy(provider),
        ],
        risk_manager=RiskManager(),
        repository=repository,
    )
    candidates = runner.run_once()
    assert len(candidates) >= 1
    strong = repository.get_latest_candidate_for_market("mock_weather_strong_yes")
    assert strong is not None
    assert strong["risk_status"] == "PASS"
    assert strong["action_status"] == "SIMULATE"
    assert repository.get_latest_weather_descriptor("mock_weather_strong_yes") is not None
    assert repository.get_latest_evidence_pack("mock_weather_strong_yes") is not None
    assert repository.get_latest_weather_view("mock_weather_strong_yes") is not None
    assert repository.get_latest_probability_view("mock_weather_strong_yes") is not None


def test_weather_resolve_api(client):
    response = client.post(
        "/api/weather/resolve",
        json={
            "market_id": "api_weather_tokyo",
            "question": "Will Tokyo high temperature exceed 30C on June 1?",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["descriptor"]["city"] == "Tokyo"
    assert data["descriptor"]["target_date"] == "2026-06-01"
    assert data["descriptor"]["threshold"] == 30
    assert data["descriptor"]["direction"] == "ABOVE"


def test_weather_probability_api(client):
    response = client.post(
        "/api/weather/probability",
        json={
            "market_id": "api_weather_tokyo_prob",
            "question": "Will Tokyo high temperature exceed 30C on June 1?",
            "yes_price": 0.52,
            "no_price": 0.49,
            "liquidity": 1000,
            "spread": 0.03,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["probability"]["engine_id"] == "gaussian_v0"
    assert 0.67 < data["probability"]["model_probability"] < 0.70
    assert data["latest_evidence_pack"] is not None
    assert data["latest_weather_view"] is not None


def test_workstation_api_after_scan(client):
    scan = client.post("/api/opportunities/scan")
    assert scan.status_code == 200
    response = client.get("/api/workstation/mock_weather_strong_yes")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["market_id"] == "mock_weather_strong_yes"
    assert data["candidate"] is not None
    assert data["descriptor"] is not None
    assert data["evidence_pack"] is not None
    assert data["sources"] is not None
    assert data["weather_view"] is not None
    assert data["probability_view"] is not None
    assert data["descriptor"]["city"] == "Tokyo"
    assert data["weather_view"]["expected_value"] == 31.2
    assert 0.67 < data["probability_view"]["model_probability"] < 0.70


def test_pwb02_does_not_enable_live_execute(client):
    response = client.post(
        "/api/settings/mode",
        json={"mode": "LIVE_EXECUTE"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "LIVE_EXECUTE" in data["message"]
    mode = client.get("/api/settings/mode").json()
    assert mode["mode"] != "LIVE_EXECUTE"
