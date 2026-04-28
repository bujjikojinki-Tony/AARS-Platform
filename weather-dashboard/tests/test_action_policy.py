from __future__ import annotations

import json

from weather_dashboard.ui.action_policy import decide_action_visibility


def _policy_file(tmp_path):
    path = tmp_path / "action_visibility_policy.json"
    path.write_text(
        json.dumps(
            {
                "policy_id": "action_visibility_policy.test.v1",
                "rules": [
                    {
                        "action": "create_pending_intent",
                        "allowed_pages": ["command"],
                        "requires_market_id": True,
                        "requires_gate_allow": True,
                        "requires_operator_reason": True,
                        "creates_intent": True,
                    },
                    {
                        "action": "run_dry_run_check",
                        "allowed_pages": ["command"],
                        "requires_pending_intent": True,
                        "requires_gateway_available": True,
                    },
                    {
                        "action": "live_execute",
                        "allowed_pages": ["command"],
                        "requires_gate_allow": True,
                        "requires_valid_approval": True,
                        "requires_live_mode_enabled": True,
                        "changes_gate": True,
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def test_action_policy_blocks_action_on_wrong_page(tmp_path) -> None:
    decision = decide_action_visibility(
        "create_pending_intent",
        page="opportunity_board",
        context={"market_id": "m1", "gate_allow": True, "operator_reason": "review"},
        policy_path=_policy_file(tmp_path),
    )

    assert decision.disabled is True
    assert "not allowed" in decision.reason


def test_action_policy_requires_gate_allow_for_pending_intent(tmp_path) -> None:
    decision = decide_action_visibility(
        "create_pending_intent",
        page="command",
        context={"market_id": "m1", "gate_allow": False, "operator_reason": "review"},
        policy_path=_policy_file(tmp_path),
    )

    assert decision.disabled is True
    assert decision.reason == "Requires gate allow."


def test_action_policy_allows_dry_run_only_with_pending_intent(tmp_path) -> None:
    blocked = decide_action_visibility(
        "run_dry_run_check",
        page="command",
        context={"pending_intent": False, "gateway_available": True},
        policy_path=_policy_file(tmp_path),
    )
    allowed = decide_action_visibility(
        "run_dry_run_check",
        page="command",
        context={"pending_intent": True, "gateway_available": True},
        policy_path=_policy_file(tmp_path),
    )

    assert blocked.disabled is True
    assert blocked.reason == "Requires pending intent."
    assert allowed.allowed is True


def test_action_policy_live_execute_requires_all_live_gates(tmp_path) -> None:
    decision = decide_action_visibility(
        "live_execute",
        page="command",
        context={"gate_allow": True, "valid_approval": True, "live_mode_enabled": False},
        policy_path=_policy_file(tmp_path),
    )

    assert decision.disabled is True
    assert decision.reason == "Requires live mode to be enabled."
    assert decision.changes_gate is True
