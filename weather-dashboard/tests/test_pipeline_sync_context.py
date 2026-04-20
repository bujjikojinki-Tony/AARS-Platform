from weather_dashboard.ui.pipeline_sync_context import build_pipeline_sync_context


def test_build_pipeline_sync_context_aligned() -> None:
    context = build_pipeline_sync_context(
        selected_market_id="m1",
        operator_context={"market_id": "m1"},
        last_sync_result={
            "market_id": "m1",
            "ok": True,
            "ran_at": "2026-04-19T01:00:00+00:00",
        },
    )

    assert context["operator_matches_selected"] is True
    assert context["last_sync_matches_selected"] is True
    assert context["last_sync_ok"] is True
    assert context["last_sync_ran_at"] == "2026-04-19T01:00:00+00:00"


def test_build_pipeline_sync_context_detects_mismatch() -> None:
    context = build_pipeline_sync_context(
        selected_market_id="m1",
        operator_context={"market_id": "m2"},
        last_sync_result={"market_id": "m3", "ok": False},
    )

    assert context["operator_matches_selected"] is False
    assert context["last_sync_matches_selected"] is False
    assert context["last_sync_ok"] is False
