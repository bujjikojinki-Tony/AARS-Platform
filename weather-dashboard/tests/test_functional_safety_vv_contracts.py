from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_global_hmi_accessibility_controls_are_present() -> None:
    app_source = _read("src/weather_dashboard/app.py")

    assert ":focus-visible" in app_source
    assert "prefers-reduced-motion" in app_source
    assert "color-scheme: dark" in app_source


def test_sidebar_runtime_status_card_has_live_heartbeat_and_second_clock() -> None:
    app_source = _read("src/weather_dashboard/app.py")

    assert "dash-runtime-spinner" in app_source
    assert "spinCross" in app_source
    assert "setInterval(tickUtcClock, 1000)" in app_source


def test_page_context_helpers_and_view_contracts_are_explicit() -> None:
    app_source = _read("src/weather_dashboard/app.py")
    workstation_source = _read("src/weather_dashboard/ui/market_workstation_page.py")
    command_source = _read("src/weather_dashboard/ui/r5_pages.py")

    assert "_build_page_context_payload" in app_source
    assert '"page_context"' in workstation_source
    assert "build_command_context_view" in command_source
    assert '"command_context_view.v1"' in command_source
    assert "source_page" in workstation_source
    assert "target_page" in workstation_source
    assert "selected_market_id" in workstation_source
    assert "entry_context" in workstation_source
    assert "source_page" in command_source
    assert "target_page" in command_source
    assert "selected_market_id" in command_source
    assert "entry_context" in command_source


def test_settings_high_risk_actions_have_explicit_confirmation_gates() -> None:
    settings_source = _read("src/weather_dashboard/ui/settings_pages.py")

    assert "Confirm critical rule disable" in settings_source
    assert "Confirm critical source disable" in settings_source
    assert "Confirm maintenance action" in settings_source
    assert "requires_confirmation" in settings_source


def test_monitoring_signals_degrades_when_plotly_is_absent() -> None:
    signals_source = _read("src/weather_dashboard/ui/monitoring_signals_panel.py")

    assert "go = None" in signals_source
    assert "chart unavailable because Plotly is not installed" in signals_source
    assert "render_chart_legend_card" in signals_source
    assert "render_legend_card" in signals_source
    assert "default_state_legend_items" in signals_source
    assert "default_signal_trend_legend_items" in signals_source


def test_shared_legend_registry_is_reused_across_research_pages() -> None:
    compact_source = _read("src/weather_dashboard/ui/compact_panel.py")
    evidence_source = _read("src/weather_dashboard/ui/market_evidence_chart.py")
    charts_source = _read("src/weather_dashboard/ui/r5_pages.py")
    workstation_source = _read("src/weather_dashboard/ui/market_workstation_page.py")

    assert "def default_state_legend_items" in compact_source
    assert "def default_market_evidence_curve_legend_items" in compact_source
    assert "def default_signal_trend_legend_items" in compact_source
    assert "default_state_legend_items" in evidence_source
    assert "default_market_evidence_curve_legend_items" in evidence_source
    assert "default_state_legend_items" in charts_source
    assert "default_market_evidence_curve_legend_items" in charts_source
    assert "default_state_legend_items" in workstation_source
    assert "default_market_evidence_curve_legend_items" in workstation_source


def test_target_hmi_files_do_not_contain_known_fake_interaction_markers() -> None:
    target_files = [
        "src/weather_dashboard/ui/monitoring_signals_panel.py",
        "src/weather_dashboard/ui/operations_monitor_page.py",
        "src/weather_dashboard/ui/r5_pages.py",
        "src/weather_dashboard/ui/settings_pages.py",
    ]
    forbidden = [
        'href="#"',
        "href='#'",
        "signals-subnav",
        "poly-action-button",
        "settings-tabs",
        "View Full History ↗",
        "⊕",
        "◉",
    ]

    combined = "\n".join(_read(path) for path in target_files)

    for marker in forbidden:
        assert marker not in combined


def test_operations_monitor_drops_stale_focus_markets_not_in_inventory() -> None:
    from weather_dashboard.ui.operations_monitor_page import _poly_enrich_focus_markets

    enriched = _poly_enrich_focus_markets(
        [
            {"market_id": "Shanghai.station_temperature", "city": "Shanghai"},
            {"market_id": "NewYork.rainfall", "city": "New York"},
        ],
        [{"market_id": "NewYork.rainfall", "city": "New York", "can_execute": False}],
    )

    assert [item["market_id"] for item in enriched] == ["NewYork.rainfall"]


def test_operations_monitor_removes_static_fake_toolbar_controls_and_has_viewport_breakpoints() -> None:
    ops_source = _read("src/weather_dashboard/ui/operations_monitor_page.py")

    assert 'All Markets <span>⌄</span>' not in ops_source
    assert "Search market, city, question...</div>" not in ops_source
    assert "@media (min-height: 2100px)" in ops_source
    assert "@media (max-height: 1399px)" in ops_source


def test_r5_command_available_actions_explain_status_cards_not_buttons() -> None:
    r5_source = _read("src/weather_dashboard/ui/r5_pages.py")

    assert "Status card only. Use the buttons below to execute this action." in r5_source
    assert "Action glyphs are status hints only. The buttons below are the live controls." in r5_source
    assert "@media (min-height: 2100px)" in r5_source
    assert "@media (max-height: 1399px)" in r5_source


def test_research_direction_is_visible_in_entry_surfaces() -> None:
    opportunity_source = _read("src/weather_dashboard/ui/opportunity_board_panel.py")
    monitor_source = _read("src/weather_dashboard/ui/operations_monitor_page.py")

    assert "RESEARCH DIRECTION" in opportunity_source
    assert "Research Direction" in monitor_source
    assert "gate_stack_api.v1_only" in opportunity_source
