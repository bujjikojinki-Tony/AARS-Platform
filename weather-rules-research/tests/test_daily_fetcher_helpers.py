from weather_rules_research.official_obs.daily_fetcher import DailySettlementFetcher


def test_map_variable_to_datatype() -> None:
    assert DailySettlementFetcher._map_variable_to_datatype("daily_max_temperature") == "TMAX"
    assert DailySettlementFetcher._map_variable_to_datatype("daily_min_temperature") == "TMIN"
    assert DailySettlementFetcher._map_variable_to_datatype("daily_precipitation_sum") == "PRCP"


def test_extract_cdo_value() -> None:
    payload = {
        "results": [
            {"date": "2026-04-12T00:00:00", "datatype": "TMAX", "value": 27.2}
        ]
    }

    value = DailySettlementFetcher._extract_cdo_value(payload)
    assert value == 27.2


def test_variable_spec_includes_units() -> None:
    spec = DailySettlementFetcher._variable_spec("daily_precipitation_sum")

    assert spec["datatype"] == "PRCP"
    assert spec["unit"] == "mm"
