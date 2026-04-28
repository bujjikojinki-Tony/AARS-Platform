from __future__ import annotations

from weather_telegram_console.bot.formatters.opportunity_board_card import format_opportunity_board_card


def test_format_opportunity_board_card_includes_top_rows() -> None:
    text = format_opportunity_board_card(
        {
            "schema_version": "opportunity_board_view.v1",
            "row_count": 1,
            "summary": {"city_count": 1, "family_count": 1, "high_opportunity_count": 1, "top_model": "ECMWF", "top_action": "prioritize_review"},
            "family_anomaly_summary": {
                "schema_version": "family_anomaly_summary.v1",
                "family_scan_status": "canonical_only",
                "top_family": "sea_ice_extent",
                "top_score": 0.91,
                "top_bucket": "high",
            },
            "rows": [
                {
                    "city": "Shanghai",
                    "market_family": "station_temperature",
                    "opportunity_score": 0.82,
                    "difficulty_score": 0.33,
                    "difficulty_label": "easy",
                    "best_model": "ECMWF",
                    "recommended_action": "prioritize_review",
                    "gate_risk_summary": "manual_advisory_only",
                    "seeded_from_manual_research": True,
                    "source_origin": "image_2_manual_research",
                    "manual_confidence": "high",
                    "alert_count": 2,
                    "anomaly_count": 1,
                    "upstream_refs": {"market_ids": ["397991"]},
                }
            ],
        }
    )

    assert "AARS Opportunity Board" in text
    assert "Shanghai" in text
    assert "station_temperature" in text
    assert "prioritize_review" in text
    assert "/market 397991" in text
    assert "image_2_manual_research" in text
    assert "Family Scan Status" in text
    assert "sea_ice_extent" in text


def test_format_opportunity_board_card_city_detail() -> None:
    text = format_opportunity_board_card(
        {
            "schema_version": "city_opportunity.v1",
            "selected_city": "Shanghai",
            "row_count": 1,
            "summary": {"city_count": 1, "family_count": 1},
            "family_anomaly_summary": {
                "schema_version": "family_anomaly_summary.v1",
                "family_scan_status": "canonical_only",
                "top_family": "sea_ice_extent",
                "top_score": 0.91,
                "top_bucket": "high",
            },
            "rows": [
                {
                    "city": "Shanghai",
                    "market_family": "station_temperature",
                    "opportunity_score": 0.82,
                    "difficulty_label": "easy",
                    "best_model": "ECMWF",
                    "recommended_action": "open_workstation",
                    "latest_alert_severity": "amber",
                    "latest_anomaly_score": 0.74,
                    "gate_risk_summary": "review_and_watch",
                    "alert_count": 2,
                    "anomaly_count": 1,
                    "upstream_refs": {"market_ids": ["397991"]},
                }
            ],
        }
    )

    assert "City Detail" in text
    assert "Top Family" in text
    assert "Next Step" in text
