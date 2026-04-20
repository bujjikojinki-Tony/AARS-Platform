from weather_dashboard.ui.command_metric_cards import _fmt_percent, _tone


def test_command_metric_card_tones_highlight_blockers_and_ready_states():
    assert _tone("READY") == "ok"
    assert _tone("blocked") == "block"
    assert _tone("manual_advisory_only") == "warn"
    assert _tone("something_else") == "neutral"


def test_command_metric_card_percent_formatting():
    assert _fmt_percent(0.42) == "42.0%"
    assert _fmt_percent(None) == "-"
