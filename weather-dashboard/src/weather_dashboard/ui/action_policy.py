from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from weather_dashboard.settings import UI_ACTION_VISIBILITY_POLICY_JSON


@dataclass(frozen=True)
class ActionDecision:
    action: str
    allowed: bool
    disabled: bool
    reason: str
    policy_ref: str
    changes_gate: bool = False
    creates_intent: bool = False


def decide_action_visibility(
    action: str,
    *,
    page: str,
    context: dict[str, Any] | None = None,
    policy_path: Path = UI_ACTION_VISIBILITY_POLICY_JSON,
) -> ActionDecision:
    policy = _load_policy(policy_path)
    policy_ref = str(policy.get("policy_id") or policy_path.name)
    rule = _find_rule(policy, action)
    ctx = context if isinstance(context, dict) else {}

    if not rule:
        return ActionDecision(
            action=action,
            allowed=False,
            disabled=True,
            reason=f"Action `{action}` is not defined in action visibility policy.",
            policy_ref=policy_ref,
        )

    allowed_pages = {str(item) for item in rule.get("allowed_pages") or []}
    if allowed_pages and page not in allowed_pages:
        return _blocked(action, rule, policy_ref, f"Action is not allowed on page `{page}`.")

    checks = [
        ("requires_market_id", bool(ctx.get("market_id")), "Requires selected market id."),
        ("requires_pending_intent", bool(ctx.get("pending_intent")), "Requires pending intent."),
        ("requires_gateway_available", bool(ctx.get("gateway_available", True)), "Gateway is unavailable."),
        ("requires_gate_allow", bool(ctx.get("gate_allow")), "Requires gate allow."),
        ("requires_valid_approval", bool(ctx.get("valid_approval")), "Requires valid approval."),
        ("requires_live_mode_enabled", bool(ctx.get("live_mode_enabled")), "Requires live mode to be enabled."),
        ("requires_operator_reason", bool(str(ctx.get("operator_reason") or "").strip()), "Requires operator reason."),
        ("requires_confirmation", bool(ctx.get("confirmed")), "Requires explicit confirmation."),
    ]
    for field, passed, reason in checks:
        if bool(rule.get(field)) and not passed:
            return _blocked(action, rule, policy_ref, reason)

    return ActionDecision(
        action=action,
        allowed=True,
        disabled=False,
        reason="Allowed by action visibility policy.",
        policy_ref=policy_ref,
        changes_gate=bool(rule.get("changes_gate")),
        creates_intent=bool(rule.get("creates_intent")),
    )


def _blocked(action: str, rule: dict[str, Any], policy_ref: str, reason: str) -> ActionDecision:
    return ActionDecision(
        action=action,
        allowed=False,
        disabled=True,
        reason=reason,
        policy_ref=policy_ref,
        changes_gate=bool(rule.get("changes_gate")),
        creates_intent=bool(rule.get("creates_intent")),
    )


def _load_policy(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"policy_id": "action_visibility_policy.unavailable", "rules": []}
    return payload if isinstance(payload, dict) else {"policy_id": "action_visibility_policy.invalid", "rules": []}


def _find_rule(policy: dict[str, Any], action: str) -> dict[str, Any]:
    for rule in policy.get("rules") or []:
        if isinstance(rule, dict) and str(rule.get("action") or "") == action:
            return rule
    return {}
