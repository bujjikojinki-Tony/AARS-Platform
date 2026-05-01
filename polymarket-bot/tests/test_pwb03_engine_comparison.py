from backend.models.weather import ParseConfidence
from backend.models.weather import WeatherDirection
from backend.models.weather import WeatherUnit
from backend.models.weather import WeatherView
from backend.probability.active_engine_policy import ActiveEnginePolicy
from backend.probability.probability_comparison_builder import ProbabilityComparisonBuilder
from backend.probability.probability_engine_registry import ProbabilityEngineRegistry
from backend.probability.probability_engine_runner import ProbabilityEngineRunner
from backend.probability.weather_probability_provider import WeatherProbabilityProvider
from backend.sources.mock_market_source import MockMarketSource
from backend.storage.db import init_db
from backend.storage.repositories import Repository


def _build_weather_view() -> WeatherView:
    return WeatherView(
        weather_view_id="wv_test",
        evidence_pack_id="evp_test",
        market_id="mock_weather_strong_yes",
        city="Tokyo",
        target_date="2026-06-01",
        expected_value=31.2,
        expected_range_low=28.7,
        expected_range_high=33.7,
        sigma=2.5,
        threshold=30,
        direction=WeatherDirection.ABOVE,
        unit=WeatherUnit.C,
        confidence=ParseConfidence.MEDIUM,
    )


def test_registry_policy_runner_and_comparison(tmp_path):
    db_path = tmp_path / "pwb03_engine_comparison.sqlite"
    init_db(str(db_path))
    repo = Repository(str(db_path))
    registry = ProbabilityEngineRegistry(repo)

    primary = registry.get_primary_engine_config()
    shadows = registry.get_shadow_engine_configs()

    assert primary is not None
    assert primary["engine_id"] == "gaussian_v0"
    assert primary["engine_type"] == "PRIMARY"
    assert len(shadows) == 2
    assert {shadow["engine_id"] for shadow in shadows} == {
        "deb_shadow_v0",
        "emos_shadow_v0",
    }

    policy = ActiveEnginePolicy()
    ok, reason = policy.validate_active_engine(primary)
    assert ok is True
    assert "accepted as active" in reason
    for shadow in shadows:
        ok, reason = policy.validate_active_engine(shadow)
        assert ok is False
        assert "PRIMARY" in reason or "primary" in reason

    provider = WeatherProbabilityProvider(
        repository=repo,
        default_year=2026,
        allow_network=False,
        default_sigma=2.5,
    )
    market = MockMarketSource().fetch_markets()[0]
    probability_view = provider.build_probability_view(market)
    latest_weather_view = repo.get_latest_weather_view(market.market_id)
    assert latest_weather_view is not None

    weather_view = _build_weather_view()
    weather_view.weather_view_id = probability_view.weather_view_id
    weather_view.evidence_pack_id = probability_view.weather_view_id.replace("wv", "evp")

    runner = ProbabilityEngineRunner(repository=repo, registry=registry)
    runs = runner.run_all(weather_view)
    comparison = ProbabilityComparisonBuilder().build(runs)
    repo.save_probability_comparison(comparison)

    assert len(runs) == 3
    assert comparison.active_engine_id == "gaussian_v0"
    assert comparison.active_probability == runs[0].model_probability
    assert comparison.disagreement_level.value == "NONE"

    stored = repo.get_latest_probability_comparison(weather_view.market_id)
    assert stored is not None
    assert stored["active_engine_id"] == "gaussian_v0"
    assert len(stored["engine_runs"]) == 3
