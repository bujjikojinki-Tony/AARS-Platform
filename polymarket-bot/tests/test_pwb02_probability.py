from backend.models.weather import ParseConfidence
from backend.models.weather import WeatherDirection
from backend.models.weather import WeatherUnit
from backend.models.weather import WeatherView
from backend.probability.gaussian_probability_engine import GaussianProbabilityEngine
from backend.probability.probability_view_builder import ProbabilityViewBuilder


def test_gaussian_probability_above():
    view = WeatherView(
        weather_view_id="wv_test",
        evidence_pack_id="evp_test",
        market_id="mkt_test",
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
    probability, warnings = GaussianProbabilityEngine().compute(view)
    assert 0.67 < probability < 0.70
    assert warnings == []


def test_gaussian_probability_below():
    view = WeatherView(
        weather_view_id="wv_test",
        evidence_pack_id="evp_test",
        market_id="mkt_test",
        city="Tokyo",
        target_date="2026-06-01",
        expected_value=31.2,
        expected_range_low=28.7,
        expected_range_high=33.7,
        sigma=2.5,
        threshold=30,
        direction=WeatherDirection.BELOW,
        unit=WeatherUnit.C,
        confidence=ParseConfidence.MEDIUM,
    )
    probability, warnings = GaussianProbabilityEngine().compute(view)
    assert 0.30 < probability < 0.33
    assert warnings == []


def test_probability_view_builder():
    view = WeatherView(
        weather_view_id="wv_test",
        evidence_pack_id="evp_test",
        market_id="mkt_test",
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
    probability_view = ProbabilityViewBuilder().build(view)
    assert probability_view.engine_id == "gaussian_v0"
    assert 0.67 < probability_view.model_probability < 0.70
    assert probability_view.market_id == "mkt_test"
