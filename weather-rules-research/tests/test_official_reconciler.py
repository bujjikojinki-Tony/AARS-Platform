from weather_rules_research.official_obs.reconciler import OfficialObservationReconciler


def test_reconciler_builds_settlement_record() -> None:
    reconciler = OfficialObservationReconciler()

    payload = {
        "station_id": "KNYC",
        "target_date": "2026-04-12",
        "variable_name": "daily_max_temperature",
        "official_value": 27.2,
        "unit": "C",
        "source": "nws_api_latest_observation",
        "source_url": "https://api.weather.gov/stations/KNYC/observations/latest",
        "raw_payload_ref": "data/raw/official_station_obs/nws_latest_KNYC.json",
        "quality_flag": None,
        "notes": "Latest station observation from NWS API",
    }

    record = reconciler.to_settlement_record(payload)

    assert record.station_id == "KNYC"
    assert record.target_date == "2026-04-12"
    assert record.variable_name == "daily_max_temperature"
    assert record.official_value == 27.2
    assert record.unit == "C"


def test_reconciler_validation_detects_missing_official_value() -> None:
    reconciler = OfficialObservationReconciler()

    payload = {
        "station_id": "KNYC",
        "target_date": "2026-04-12",
        "variable_name": "daily_max_temperature",
        "official_value": None,
        "unit": "C",
        "source": "ncei_cdo_stub",
    }

    record = reconciler.to_settlement_record(payload)
    issues = reconciler.validate_for_backtest(record)

    assert "missing official_value" in issues
