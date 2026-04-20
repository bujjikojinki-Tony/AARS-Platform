import json

from weather_dashboard.loaders.dashboard_rows_loader import DashboardRowsLoader
from weather_dashboard.loaders.signal_loader import SignalLoader
from weather_dashboard.loaders.market_bundle_loader import MarketBundleLoader
from weather_dashboard.loaders.realtime_forecast_loader import RealtimeForecastLoader
from weather_dashboard.loaders.realtime_market_loader import RealtimeMarketLoader


def test_dashboard_rows_loader(tmp_path):
    path = tmp_path / "rows.json"
    path.write_text(
        json.dumps([{"market_id": "m1", "confidence_adjusted_gap": 0.8}]),
        encoding="utf-8",
    )

    loader = DashboardRowsLoader()
    df = loader.load_df(path)

    assert len(df) == 1
    assert df.iloc[0]["market_id"] == "m1"


def test_signal_loader(tmp_path):
    path = tmp_path / "signal.json"
    path.write_text(json.dumps({"signal_id": "sig_1"}), encoding="utf-8")

    loader = SignalLoader()
    payload = loader.load(path)

    assert payload["signal_id"] == "sig_1"


def test_market_bundle_loader(tmp_path):
    path = tmp_path / "bundles.json"
    path.write_text(json.dumps([{"market": {"market_id": "m1"}}]), encoding="utf-8")

    loader = MarketBundleLoader()
    payload = loader.load(path)

    assert payload[0]["market"]["market_id"] == "m1"


def test_realtime_market_loader(tmp_path):
    path = tmp_path / "realtime_market.json"
    path.write_text(json.dumps({"market_id": "m1", "market_band": "28"}), encoding="utf-8")

    loader = RealtimeMarketLoader()
    payload = loader.load(path)

    assert payload["market_id"] == "m1"
    assert payload["market_band"] == "28"


def test_realtime_market_loader_load_many(tmp_path):
    path1 = tmp_path / "market_realtime_simple_global_temperature_index.json"
    path2 = tmp_path / "market_realtime_simple_sea_ice_extent.json"
    path1.write_text(
        json.dumps({"market_id": "m1", "updated_at": "2026-04-11T12:00:00+00:00"}),
        encoding="utf-8",
    )
    path2.write_text(
        json.dumps({"market_id": "m2", "updated_at": "2026-04-11T12:01:00+00:00"}),
        encoding="utf-8",
    )

    loader = RealtimeMarketLoader()
    payload = loader.load_many(tmp_path / "market_realtime_simple_*.json")

    assert len(payload) == 2
    assert payload[0]["market_id"] == "m2"


def test_realtime_forecast_loader(tmp_path):
    path = tmp_path / "realtime_forecast.json"
    path.write_text(json.dumps({"market_id": "m1", "model_band": "28"}), encoding="utf-8")

    loader = RealtimeForecastLoader()
    payload = loader.load(path)

    assert payload["market_id"] == "m1"
    assert payload["model_band"] == "28"


def test_realtime_forecast_loader_load_many(tmp_path):
    path1 = tmp_path / "forecast_realtime_snapshot_m1.json"
    path2 = tmp_path / "forecast_realtime_snapshot_m2.json"
    path1.write_text(
        json.dumps({"market_id": "m1", "timestamp": "2026-04-11T12:00:00+00:00"}),
        encoding="utf-8",
    )
    path2.write_text(
        json.dumps({"market_id": "m2", "timestamp": "2026-04-11T12:01:00+00:00"}),
        encoding="utf-8",
    )

    loader = RealtimeForecastLoader()
    payload = loader.load_many(tmp_path / "forecast_realtime_snapshot_*.json")

    assert len(payload) == 2
    assert payload[0]["market_id"] == "m2"
