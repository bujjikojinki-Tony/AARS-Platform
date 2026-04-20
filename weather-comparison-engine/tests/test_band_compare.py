from weather_comparison_engine.compare.band_compare import BandCompare


def test_band_distance():
    cmp = BandCompare()
    assert cmp.distance("28", "27") == 1
    assert cmp.distance("29_plus", "27") == 2
    assert cmp.distance("28", "28") == 0


def test_band_distance_sea_ice_scheme():
    cmp = BandCompare()
    assert cmp.distance("in_range", "in_range", band_scheme="sea_ice_range_3way") == 0
    assert cmp.distance("below_range", "in_range", band_scheme="sea_ice_range_3way") == 1
    assert cmp.distance("above_range", "below_range", band_scheme="sea_ice_range_3way") == 2


def test_band_distance_global_temperature_index_scheme():
    cmp = BandCompare()
    assert cmp.distance("top_3", "top_3", band_scheme="global_temperature_index_ordinal") == 0
    assert cmp.distance("top_2", "top_3", band_scheme="global_temperature_index_ordinal") == 1
    assert cmp.distance("top_1", "top_3", band_scheme="global_temperature_index_ordinal") == 2


def test_band_distance_precipitation_scheme():
    cmp = BandCompare()
    assert cmp.distance("in_range", "in_range", band_scheme="precipitation_range_3way") == 0
    assert cmp.distance("below_range", "in_range", band_scheme="precipitation_range_3way") == 1
    assert cmp.distance("above_range", "below_range", band_scheme="precipitation_range_3way") == 2


def test_band_distance_snowfall_and_wind_schemes():
    cmp = BandCompare()
    assert cmp.distance("in_range", "above_range", band_scheme="snowfall_range_3way") == 1
    assert cmp.distance("below_range", "above_range", band_scheme="wind_speed_range_3way") == 2
