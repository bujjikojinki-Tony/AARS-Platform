from polymarket_weather_ingest.ingest.market_band_scheme import derive_market_band_spec


def test_derive_market_band_spec_for_sea_ice_range():
    spec = derive_market_band_spec(
        "Will the minimum Arctic sea ice extent this summer be between 4.8m & 5m square kilometers?",
        0.63,
    )

    assert spec.scheme == "sea_ice_range_3way"
    assert spec.band == "in_range"
    assert spec.lower_threshold == 4.8
    assert spec.upper_threshold == 5.0
    assert spec.unit == "million_sq_km"


def test_derive_market_band_spec_for_temperature_uses_probability_buckets():
    spec = derive_market_band_spec("Highest temperature in Central Park on Apr 12?", 0.81)

    assert spec.scheme == "temperature_4_bucket"
    assert spec.band == "29_plus"


def test_derive_market_band_spec_for_global_temperature_index():
    spec = derive_market_band_spec("Will 2026 be the third-hottest year on record?", 0.52)

    assert spec.scheme == "global_temperature_index_ordinal"
    assert spec.band == "top_3"


def test_derive_market_band_spec_for_precipitation_between_range():
    spec = derive_market_band_spec(
        "Will rainfall in Shanghai on Apr 18 be between 10mm and 20mm?",
        0.52,
    )

    assert spec.scheme == "precipitation_range_3way"
    assert spec.band == "in_range"
    assert spec.lower_threshold == 10.0
    assert spec.upper_threshold == 20.0
    assert spec.unit == "mm"


def test_derive_market_band_spec_for_precipitation_less_than():
    spec = derive_market_band_spec(
        "Will rainfall in Shanghai on Apr 18 be less than 10mm?",
        0.52,
    )

    assert spec.scheme == "precipitation_range_3way"
    assert spec.band == "below_range"
    assert spec.upper_threshold == 10.0


def test_derive_market_band_spec_for_snowfall_above_range():
    spec = derive_market_band_spec(
        "Will snowfall in Shanghai on Apr 18 be above 5cm?",
        0.52,
    )

    assert spec.scheme == "snowfall_range_3way"
    assert spec.band == "above_range"
    assert spec.lower_threshold == 5.0
    assert spec.unit == "cm"


def test_derive_market_band_spec_for_wind_between_range():
    spec = derive_market_band_spec(
        "Will wind speed in Shanghai on Apr 18 be between 20 km/h and 40 km/h?",
        0.52,
    )

    assert spec.scheme == "wind_speed_range_3way"
    assert spec.band == "in_range"
    assert spec.lower_threshold == 20.0
    assert spec.upper_threshold == 40.0
    assert spec.unit == "km_h"
