from weather_dashboard.ui.raw_json_panel import render_raw_json_panel


def test_raw_json_panel_smoke():
    render_raw_json_panel(
        signal_payload={"signal_id": "sig_1"},
        market_bundles=[{"market": {"market_id": "m1"}}],
        rulebook_payload={"version": "0.1"},
    )

