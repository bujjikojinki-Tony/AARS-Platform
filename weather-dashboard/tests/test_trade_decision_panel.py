from __future__ import annotations

from weather_dashboard.ui import trade_decision_panel


def test_trade_decision_panel_includes_promotion_card(monkeypatch) -> None:
    captured: list[dict] = []

    monkeypatch.setattr(trade_decision_panel, "render_panel_title", lambda *args, **kwargs: None)
    monkeypatch.setattr(trade_decision_panel, "render_compact_note", lambda *args, **kwargs: None)
    monkeypatch.setattr(trade_decision_panel.st, "checkbox", lambda *args, **kwargs: False)
    monkeypatch.setattr(
        trade_decision_panel,
        "_render_trade_decision_cards",
        lambda cards: captured.extend(cards),
    )

    trade_decision_panel.render_trade_decision_panel(
        market_snapshot={
            "market_id": "m1",
            "market_probability": 0.61,
            "yes_price": 0.61,
            "no_price": 0.39,
            "favored_side": "yes",
        },
        forecast_snapshot={"market_id": "m1"},
        probability_state={
            "probability_mode": "shadow_calibrated_candidate",
            "execution_constraint": "dry_run_only",
            "promotion_state": {
                "probability_mode": "shadow_calibrated_candidate",
                "execution_constraint": "dry_run_only",
                "promotion_reason": "candidate_thresholds_passed",
                "demotion_reason": None,
                "approved_for_live": False,
            },
            "promotion_reason": "candidate_thresholds_passed",
            "demotion_reason": None,
        },
        comparison_row={"comparison_status": "aligned", "confidence_score": 0.74},
    )

    assert len(captured) == 5
    titles = [card["title"] for card in captured]
    assert "Promotion" in titles
    promotion_card = next(card for card in captured if card["title"] == "Promotion")
    assert promotion_card["value"] == "shadow_calibrated_candidate"
    assert ("Reason", "candidate_thresholds_passed") in promotion_card["rows"]
