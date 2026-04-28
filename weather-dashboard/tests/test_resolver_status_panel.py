from weather_dashboard.ui.compact_panel import sanitize_text, semantic_tone
from weather_dashboard.ui.resolver_status_panel import _find_rule, build_resolver_status_summary


def test_resolver_status_summary_surfaces_source_contract():
    summary = build_resolver_status_summary(
        {
            "market_id": "379803",
            "market_question": "Highest temperature in Shanghai on April 16?",
            "resolver_status": "matched",
            "resolver_reason": "matched_by_market_id",
            "resolver_name": "station_temperature_resolver",
            "resolver_confidence": 0.93,
            "market_family": "station_temperature",
            "resolution_scope": "station_weather",
            "supported_by_current_pipeline": True,
            "required_data_source": "wunderground_zspd",
            "required_sources": [
                "wunderground_zspd_history",
                "wunderground_zspd_realtime",
                "forecast_station_mapping",
            ],
            "settlement_source_type": "station_observation",
            "official_vs_proxy_source": "official",
            "source_match_grade": "exact_station",
            "official_source_url": "https://www.wunderground.com/history/weekly/cn/shanghai/ZSPD",
            "source_note": "Shanghai weather markets are pinned to Pudong Airport (ZSPD).",
        }
    )

    assert summary is not None
    assert summary["note"] is None
    assert summary["official_source_url"] == "https://www.wunderground.com/history/weekly/cn/shanghai/ZSPD"
    labels = {label: value for label, value in summary["items"]}
    assert labels["Required Inputs"] == "wunderground_zspd_history, wunderground_zspd_realtime, forecast_station_mapping"
    assert labels["Source Policy"] == "official"
    assert labels["Source Match"] == "exact_station"


def test_resolver_status_summary_warns_for_family_only_match():
    summary = build_resolver_status_summary(
        {
            "market_id": "m1",
            "resolver_status": "matched",
            "official_vs_proxy_source": "fallback",
            "source_match_grade": "family_only",
        }
    )

    assert summary is not None
    assert "partially aligned" in str(summary["note"])


def test_resolver_status_panel_does_not_fallback_to_first_rule():
    rule = _find_rule(
        {
            "rules": [
                {"market_id": "A", "station_name": "Alpha"},
                {"market_id": "B", "station_name": "Beta"},
            ]
        },
        "missing",
    )

    assert rule is None


def test_compact_panel_sanitizes_html_tags():
    assert sanitize_text("<div class='x'>Promotion OK</div>") == "Promotion OK"


def test_semantic_tone_highlights_partial_and_blocked_states():
    assert semantic_tone("Source Match Grade", "exact_station") == "ok"
    assert semantic_tone("Freshness", "stale") == "warning"
    assert semantic_tone("Gate Status", "BLOCKED") == "critical"
    assert semantic_tone("Execution Constraint", "dry_run_only") == "warning"
