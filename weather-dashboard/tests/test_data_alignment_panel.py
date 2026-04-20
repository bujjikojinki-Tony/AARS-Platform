from weather_dashboard.ui.data_alignment_panel import build_data_alignment_audit


def test_data_alignment_audit_ready_when_market_ids_match():
    audit = build_data_alignment_audit(
        selected_market_snapshot={
            "market_id": "m1",
            "market_question": "Will Shanghai be hot?",
        },
        activated_market_snapshot={
            "market_id": "m1",
            "updated_at": "2026-04-17T00:00:00+00:00",
        },
        forecast_snapshot={
            "market_id": "m1",
            "model_band": "30",
            "value": 30.0,
            "source_mode": "wunderground.resolver",
            "timestamp": "2026-04-17T00:01:00+00:00",
        },
        resolver_rule={
            "market_id": "m1",
            "resolver_status": "matched",
            "market_family": "city_temperature",
            "required_data_source": "wunderground_zspd",
            "source_match_grade": "exact_station",
            "official_vs_proxy_source": "official",
            "resolver_reason": "matched station and metric",
        },
        probability_state={
            "market_id": "m1",
            "fair_value": 0.61,
            "edge": 0.04,
            "mode": "shadow",
            "calibration_status": "uncalibrated",
        },
        comparison_row={
            "market_id": "m1",
            "comparison_status": "aligned",
            "market_band": "30",
            "model_band": "30",
            "confidence_adjusted_gap": 0.0,
        },
    )

    assert audit["ready_for_bot"] is True
    assert audit["selected_market_id"] == "m1"
    assert [check["level"] for check in audit["checks"][1:]] == ["ok", "ok", "ok", "ok", "ok"]


def test_data_alignment_audit_blocks_when_pipeline_points_to_other_market():
    audit = build_data_alignment_audit(
        selected_market_snapshot={
            "market_id": "m1",
            "market_question": "Will Shanghai be hot?",
        },
        activated_market_snapshot={"market_id": "m2"},
        forecast_snapshot={"market_id": "m2", "model_band": "top_3", "value": 3},
        resolver_rule={
            "market_id": "m1",
            "resolver_status": "unmatched",
            "market_family": "unknown",
            "required_data_source": None,
            "source_match_grade": "unmatched",
            "official_vs_proxy_source": "unknown",
        },
        probability_state={"market_id": "m2"},
        comparison_row={"market_id": "m2", "comparison_status": "aligned"},
    )

    status_by_name = {check["name"]: check["status"] for check in audit["checks"]}
    level_by_name = {check["name"]: check["level"] for check in audit["checks"]}

    assert audit["ready_for_bot"] is False
    assert status_by_name["Market Input"] == "mismatch"
    assert status_by_name["Forecast"] == "mismatch"
    assert status_by_name["Resolver"] == "unmatched"
    assert status_by_name["Probability"] == "mismatch"
    assert status_by_name["Comparison"] == "mismatch"
    assert level_by_name["Resolver"] == "warn"


def test_data_alignment_audit_warns_when_resolver_is_only_family_level():
    audit = build_data_alignment_audit(
        selected_market_snapshot={"market_id": "m1", "market_question": "Will 2026 be the hottest year on record?"},
        activated_market_snapshot={"market_id": "m1"},
        forecast_snapshot={"market_id": "m1"},
        resolver_rule={
            "market_id": "m1",
            "resolver_status": "matched",
            "market_family": "global_temperature_index",
            "required_data_source": "global_temperature_index_snapshot",
            "source_match_grade": "family_only",
            "official_vs_proxy_source": "fallback",
        },
        probability_state={"market_id": "m1"},
        comparison_row={"market_id": "m1", "comparison_status": "aligned"},
    )

    resolver_check = next(check for check in audit["checks"] if check["name"] == "Resolver")

    assert resolver_check["level"] == "warn"
    assert "match=family_only" in resolver_check["detail"]
