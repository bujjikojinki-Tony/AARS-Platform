from __future__ import annotations

from importlib import import_module

__all__ = [
    "render_overview",
    "render_comparison_table",
    "render_bias_summary_panel",
    "render_signal_panel",
    "render_market_panel",
    "render_market_snapshots_panel",
    "render_live_status_panel",
    "render_history_relationship_panel",
    "render_recent_markets_panel",
    "render_realtime_snapshot_panel",
    "render_timeseries_panel",
    "render_timeline_panel",
    "render_trade_decision_panel",
    "render_detail_panel",
    "render_divergence_chart",
    "render_divergence_trend_chart",
    "render_filters",
    "render_raw_json_panel",
    "render_rule_station_panel",
    "render_opportunity_board_panel",
    "render_timeseries_placeholder",
]


def __getattr__(name: str):
    module_map = {
        "render_overview": "weather_dashboard.ui.overview",
        "render_comparison_table": "weather_dashboard.ui.comparison_table",
        "render_bias_summary_panel": "weather_dashboard.ui.bias_summary_panel",
        "render_signal_panel": "weather_dashboard.ui.signal_panel",
        "render_market_panel": "weather_dashboard.ui.market_panel",
        "render_market_snapshots_panel": "weather_dashboard.ui.market_snapshots_panel",
        "render_live_status_panel": "weather_dashboard.ui.live_status_panel",
        "render_history_relationship_panel": "weather_dashboard.ui.history_relationship_panel",
        "render_recent_markets_panel": "weather_dashboard.ui.recent_markets_panel",
        "render_realtime_snapshot_panel": "weather_dashboard.ui.realtime_snapshot_panel",
        "render_timeseries_panel": "weather_dashboard.ui.timeseries_panel",
        "render_timeline_panel": "weather_dashboard.ui.timeline_panel",
        "render_trade_decision_panel": "weather_dashboard.ui.trade_decision_panel",
        "render_detail_panel": "weather_dashboard.ui.detail_panel",
        "render_divergence_chart": "weather_dashboard.ui.divergence_chart",
        "render_divergence_trend_chart": "weather_dashboard.ui.divergence_trend_chart",
        "render_filters": "weather_dashboard.ui.filters",
        "render_raw_json_panel": "weather_dashboard.ui.raw_json_panel",
        "render_rule_station_panel": "weather_dashboard.ui.rule_station_panel",
        "render_opportunity_board_panel": "weather_dashboard.ui.opportunity_board_panel",
        "render_timeseries_placeholder": "weather_dashboard.ui.timeseries_placeholder",
    }
    module_name = module_map.get(name)
    if not module_name:
        raise AttributeError(name)
    module = import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value
