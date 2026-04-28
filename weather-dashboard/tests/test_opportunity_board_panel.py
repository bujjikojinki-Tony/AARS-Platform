from __future__ import annotations

from pathlib import Path

from weather_dashboard.ui.opportunity_board_panel import (
    _family_scan_summary,
    _filter_rows,
    _primary_market_id,
    _ranked_opportunity_table,
)


def test_filter_rows_supports_model_alert_and_anomaly_filters() -> None:
    rows = [
        {
            "city": "Shanghai",
            "market_family": "station_temperature",
            "best_model": "ECMWF",
            "difficulty_label": "easy",
            "freshness_status": "fresh",
            "recommended_action": "prioritize_review",
            "alert_count": 2,
            "anomaly_count": 1,
        },
        {
            "city": "Miami",
            "market_family": "weather_metric.wind_speed",
            "best_model": "HRRR",
            "difficulty_label": "medium",
            "freshness_status": "stale",
            "recommended_action": "review_hard_market",
            "alert_count": 0,
            "anomaly_count": 0,
        },
    ]

    filtered = _filter_rows(
        rows,
        city="Shanghai",
        family="All",
        best_model="ECMWF",
        difficulty_label="easy",
        freshness="fresh",
        action="prioritize_review",
        alert_only=True,
        anomaly_only=True,
    )

    assert len(filtered) == 1
    assert filtered[0]["city"] == "Shanghai"


def test_primary_market_id_prefers_upstream_market_refs() -> None:
    row = {
        "upstream_refs": {"market_ids": ["m_focus", "m_other"]},
        "latest_context": {"market_id": "m_latest"},
    }

    assert _primary_market_id(row) == "m_focus"


def test_primary_market_id_falls_back_to_latest_context() -> None:
    row = {
        "upstream_refs": {"market_ids": []},
        "latest_context": {"market_id": "m_latest"},
    }

    assert _primary_market_id(row) == "m_latest"


def test_family_scan_summary_uses_top_family_and_buckets() -> None:
    summary = _family_scan_summary(
        {
            "schema_version": "family_scan_report.v1",
            "input_mode": "canonical_only",
            "family_summaries": [
                {
                    "market_family": "sea_ice_extent",
                    "max_intervention_like_score": 0.91,
                    "signal_summary": "pv=2 edge=1 mismatch=0 stress=2 peer=1 high=2",
                }
            ],
            "signal_summary": {
                "price_velocity_high_count": 2,
                "edge_dislocation_high_count": 1,
                "evidence_mismatch_count": 0,
                "microstructure_stress_high_count": 2,
                "peer_outlier_count": 1,
                "intervention_like_high_count": 2,
            },
            "anomaly_bucket_counts": {"high": 1, "medium": 0, "low": 0},
        }
    )

    assert summary["status"] == "canonical_only"
    assert summary["top_family"] == "sea_ice_extent"
    assert summary["top_bucket"] == "high"
    assert "pv=2" in summary["signal_summary"]


def test_ranked_opportunity_table_uses_real_page_bounds() -> None:
    rows = [
        {
            "row_id": f"row_{index}",
            "city": f"City {index}",
            "country": "US",
            "market_family": "rainfall",
            "market_question": f"Rainfall market {index}",
            "opportunity_score": 80 - index,
            "source_precision_score": 0.8,
            "freshness_status": "LIVE",
        }
        for index in range(10)
    ]

    html = _ranked_opportunity_table(
        rows,
        "row_10",
        start_index=10,
        total_rows=128,
        page=2,
        total_pages=13,
        page_size=10,
    )

    assert "Showing 11 to 20 of 128 opportunities" in html
    assert "Page 2 / 13" in html
    assert "<td>11 ☆</td>" in html


def test_opportunity_actions_column_is_rendered_as_hint_semantics() -> None:
    source = Path("weather-dashboard/src/weather_dashboard/ui/opportunity_board_panel.py").read_text(encoding="utf-8")

    assert "availability hints only" in source
    assert "_action_hints_html" in source
    assert "Use the live buttons in the right-side panel" in source
