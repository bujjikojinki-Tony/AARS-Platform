from backend.models.weather import ParseConfidence
from backend.models.weather import WeatherDirection
from backend.models.weather import WeatherUnit
from backend.models.weather import WeatherView
from backend.probability.calibration_metrics import absolute_error
from backend.probability.calibration_metrics import brier_score
from backend.probability.calibration_metrics import probability_bucket
from backend.probability.calibration_service import CalibrationService
from backend.probability.market_outcome_service import MarketOutcomeService
from backend.probability.model_promotion_gate import ModelPromotionGate
from backend.api.routes_probability_governance import create_probability_governance_router
from backend.probability.probability_engine_registry import ProbabilityEngineRegistry
from backend.probability.probability_engine_runner import ProbabilityEngineRunner
from backend.probability.probability_comparison_builder import ProbabilityComparisonBuilder
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


def test_metrics_validate_and_bucket():
    assert round(brier_score(0.7, 1), 2) == 0.09
    assert round(absolute_error(0.7, 1), 1) == 0.3
    assert probability_bucket(0.7) == "0.6-0.8"


def test_outcome_calibration_and_promotion_flow(tmp_path):
    db_path = tmp_path / "pwb03_calibration.sqlite"
    init_db(str(db_path))
    repo = Repository(str(db_path))

    provider = WeatherProbabilityProvider(
        repository=repo,
        default_year=2026,
        allow_network=False,
        default_sigma=2.5,
    )
    market = MockMarketSource().fetch_markets()[0]
    provider.build_probability_view(market)

    latest_weather_view = repo.get_latest_weather_view(market.market_id)
    assert latest_weather_view is not None
    weather_view = _build_weather_view()
    weather_view.weather_view_id = latest_weather_view["weather_view_id"]
    weather_view.evidence_pack_id = latest_weather_view["evidence_pack_id"]

    registry = ProbabilityEngineRegistry(repo)
    runs = ProbabilityEngineRunner(repo, registry).run_all(weather_view)
    comparison = ProbabilityComparisonBuilder().build(runs)
    repo.save_probability_comparison(comparison)

    outcome = MarketOutcomeService(repo).record_outcome(
        market_id=market.market_id,
        status="RESOLVED",
        resolved_direction_hit=True,
        resolved_value=31.8,
        official_source="manual_test",
        notes="Manual resolved outcome for PWB-03 smoke test",
    )
    assert outcome.status.value == "RESOLVED"

    calibration_results = CalibrationService(repo).calibrate_market(market.market_id)
    assert len(calibration_results) == 3
    assert {result.engine_id for result in calibration_results} == {
        "gaussian_v0",
        "deb_shadow_v0",
        "emos_shadow_v0",
    }

    gaussian_decision = ModelPromotionGate(repo).evaluate("gaussian_v0")
    deb_decision = ModelPromotionGate(repo).evaluate("deb_shadow_v0")
    emos_decision = ModelPromotionGate(repo).evaluate("emos_shadow_v0")

    assert gaussian_decision.decision.value == "KEEP_PRIMARY"
    assert deb_decision.decision.value == "NEEDS_MORE_DATA"
    assert emos_decision.decision.value == "NEEDS_MORE_DATA"

    assert repo.get_latest_market_outcome(market.market_id)["resolved_direction_hit"] is True
    assert len(repo.list_calibration_results_for_market(market.market_id)) == 3


def test_probability_governance_api_routes_available(tmp_path):
    db_path = tmp_path / "pwb03_api.sqlite"
    init_db(str(db_path))
    repo = Repository(str(db_path))
    router = create_probability_governance_router(repo)
    paths = {route.path for route in router.routes}

    assert "/api/probability/engines" in paths
    assert "/api/probability/compare/{market_id}" in paths
    assert "/api/probability/comparison/{market_id}" in paths
    assert "/api/probability/outcomes" in paths
    assert "/api/probability/outcomes/{market_id}" in paths
    assert "/api/probability/calibrate/{market_id}" in paths
    assert "/api/probability/calibration/{engine_id}" in paths
    assert "/api/probability/promotion/{engine_id}" in paths
