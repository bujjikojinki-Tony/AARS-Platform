from __future__ import annotations

import weather_dashboard.ui.polymarket_connector_panel as panel


def test_build_polymarket_connector_panel_state_defaults() -> None:
    state = panel.build_polymarket_connector_panel_state()

    assert state["mode"] == "MOCK_ONLY"
    assert state["allow_polymarket_network"] is False
    assert state["read_only"] is True
    assert state["cached_markets"] == []
    assert state["preview_snapshots"] == []
    assert "network access disabled" in str(state["warnings"][0]).lower()


def test_apply_source_mode_payload_updates_mode_and_network(monkeypatch) -> None:
    monkeypatch.setitem(panel.st.session_state, panel.MODE_WIDGET_KEY, "MOCK_ONLY")
    monkeypatch.setitem(panel.st.session_state, panel.NETWORK_WIDGET_KEY, "Disabled")
    state = panel.build_polymarket_connector_panel_state()

    panel._apply_source_mode_payload(
        state,
        {
            "market_source_mode": "HYBRID",
            "allow_polymarket_network": False,
            "config": {
                "market_source_mode": "HYBRID",
                "allow_polymarket_network": False,
                "gamma_base_url": "https://gamma-api.polymarket.com",
                "clob_base_url": "https://clob.polymarket.com",
                "request_timeout_seconds": 8,
                "max_markets": 50,
                "weather_keywords": ["weather"],
            },
        },
    )

    assert state["mode"] == "HYBRID"
    assert state["allow_polymarket_network"] is False
    assert panel.st.session_state[panel.MODE_WIDGET_KEY] == "HYBRID"
    assert panel.st.session_state[panel.NETWORK_WIDGET_KEY] == "Disabled"


def test_cached_market_rows_render_prices_and_status() -> None:
    rows = panel._cached_markets_rows(
        [
            {
                "polymarket_market_id": "pm_weather_1",
                "question": "Will Tokyo high temperature exceed 30C on June 1?",
                "fetched_at": "2026-04-30T00:00:00Z",
                "active": True,
                "closed": False,
                "archived": False,
                "outcomes": ["Yes", "No"],
                "outcome_prices": [0.52, 0.49],
                "clob_token_ids": ["yes", "no"],
                "liquidity": 1000.0,
            }
        ]
    )

    assert rows[0]["market_id"] == "pm_weather_1"
    assert rows[0]["prices"] == "Yes: 0.52, No: 0.49"
    assert rows[0]["status"] == "ACTIVE"


def test_preview_snapshot_rows_format_percentages() -> None:
    rows = panel._preview_snapshot_rows(
        [
            {
                "market_id": "m1",
                "question": "Will it rain in Shanghai?",
                "yes_price": 0.61,
                "no_price": 0.39,
                "liquidity": 1000.0,
                "spread": 0.02,
                "source": "mock",
            }
        ]
    )

    assert rows[0]["yes"] == "61.0%"
    assert rows[0]["no"] == "39.0%"
    assert rows[0]["source"] == "mock"
