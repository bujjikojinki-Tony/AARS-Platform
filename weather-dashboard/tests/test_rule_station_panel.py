from weather_dashboard.ui.rule_station_panel import build_selected_rule


def test_rule_station_panel_returns_none_when_market_does_not_match():
    rules, selected = build_selected_rule(
        {
            "rules": [
                {"market_id": "A", "station_name": "Alpha"},
                {"market_id": "B", "station_name": "Beta"},
            ]
        },
        "missing",
    )

    assert len(rules) == 2
    assert selected is None


def test_rule_station_panel_finds_exact_market_match():
    _, selected = build_selected_rule(
        [
            {"market_id": "A", "station_name": "Alpha"},
            {"market_id": "B", "station_name": "Beta"},
        ],
        "B",
    )

    assert selected == {"market_id": "B", "station_name": "Beta"}
