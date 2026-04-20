from weather_rules_research.sea_ice import (
    SeaIceExtentLoader,
    classify_sea_ice_band,
    extract_sea_ice_extent_value,
)


def test_sea_ice_extent_loader_reads_snapshot(tmp_path):
    path = tmp_path / "sea_ice_extent_snapshot.json"
    path.write_text(
        '{"minimum_extent": 4.1, "unit": "million_sq_km"}',
        encoding="utf-8",
    )

    payload = SeaIceExtentLoader().load(path)

    assert payload["minimum_extent"] == 4.1


def test_extract_and_classify_sea_ice_band():
    payload = {"minimum_extent": 4.1}

    value = extract_sea_ice_extent_value(payload)
    band = classify_sea_ice_band(value, lower=4.0, upper=4.2)

    assert value == 4.1
    assert band == "in_range"


def test_classify_sea_ice_band_handles_below_and_above():
    assert classify_sea_ice_band(3.9, lower=4.0, upper=4.2) == "below_range"
    assert classify_sea_ice_band(4.3, lower=4.0, upper=4.2) == "above_range"
