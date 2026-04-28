from __future__ import annotations

import json
from pathlib import Path


def test_buy_sell_decision_policy_exists_and_respects_gate_boundary() -> None:
    path = Path("weather-comparison-engine/data/registries/opportunity_policy_registry/buy_sell_decision_policy.json")
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["policy_id"] == "buy_sell_decision_policy.v1"
    assert payload["schema_version"] == "buy_sell_decision_policy.v1"
    assert payload["applicable_scope"] == "single_market_workstation.buy_sell_research_decision"
    assert payload["required_inputs"]["market_probability_fields"] == [
        "market_implied_probability",
        "yes_price",
        "no_price",
    ]
    assert payload["required_inputs"]["fair_value_fields"] == ["fair_value", "probability_mode"]
    assert payload["required_inputs"]["edge_fields"] == ["edge"]
    assert payload["thresholds"]["research_yes_edge_min"] == 0.05
    assert payload["thresholds"]["research_no_edge_max"] == -0.05
    assert payload["execution_boundary"]["execution_permission_source"] == "gate_stack_api.v1_only"
    assert payload["execution_boundary"]["requires_can_execute"] is True
    assert "research_buy_yes" in payload["output_enums"]
    assert "research_buy_no" in payload["output_enums"]
    assert any("not execution permission" in note for note in payload["execution_boundary"]["notes"])
