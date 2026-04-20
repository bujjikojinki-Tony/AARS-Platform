from __future__ import annotations


def format_status_card(report: dict) -> str:
    current_market = report.get("current_market") or {}
    monitoring = report.get("monitoring") or {}
    probability = report.get("probability") or {}
    probability_contract = probability.get("probability_contract") or {}
    promotion_state = _extract_promotion_state(report, probability, probability_contract)
    execution = report.get("execution") or {}
    operator = report.get("operator") or {}
    mode_badge = operator.get("mode_badge") or {}
    gate_stack = report.get("gate_stack") or {}
    workers = monitoring.get("workers") or []
    worker_summary = ", ".join(
        f"{worker.get('label', 'worker')}={worker.get('status', '-')}"
        for worker in workers[:6]
        if isinstance(worker, dict)
    ) or "-"
    block_reasons = ", ".join(str(item) for item in report.get("block_reasons") or []) or "-"

    return (
        "*AARS Unified Status*\n"
        f"*Overall:* `{report.get('overall_status', '-')}`\n"
        f"*Generated At:* `{report.get('generated_at', '-')}`\n\n"
        "*Current Market*\n"
        f"*Market ID:* `{current_market.get('market_id', '-')}`\n"
        f"*Question:* {current_market.get('market_question', '-')}\n"
        f"*Comparison:* `{current_market.get('comparison_status', '-')}`\n"
        f"*Action Hint:* `{current_market.get('action_hint', '-')}`\n\n"
        "*Monitoring*\n"
        f"*Overall:* `{monitoring.get('overall_status', '-')}`\n"
        f"*Workers:* `{monitoring.get('worker_count', '-')}`\n"
        f"*Counts:* `{monitoring.get('counts', {})}`\n"
        f"*Worker Summary:* `{worker_summary}`\n\n"
        "*Probability Contract*\n"
        f"*Contract:* `{probability.get('contract_version') or probability_contract.get('contract_version', '-')}`\n"
        f"*Mode:* `{probability.get('probability_mode', '-')}`\n"
        f"*Execution Constraint:* `{probability.get('execution_constraint', '-')}`\n"
        f"*Calibration:* `{probability.get('calibration_status', '-')}`\n"
        f"*Adj Edge:* `{probability.get('confidence_adjusted_edge', '-')}`\n\n"
        "*Promotion State*\n"
        f"*State:* `{promotion_state.get('probability_mode', '-')}`\n"
        f"*Base Mode:* `{promotion_state.get('base_probability_mode', '-')}`\n"
        f"*Constraint:* `{promotion_state.get('execution_constraint', '-')}`\n"
        f"*Reason:* `{promotion_state.get('promotion_reason', '-')}`\n"
        f"*Demotion:* `{promotion_state.get('demotion_reason', '-')}`\n"
        f"*Approved For Live:* `{promotion_state.get('approved_for_live', '-')}`\n\n"
        "*Execution*\n"
        f"*Status:* `{execution.get('status', '-')}`\n"
        f"*Ready For Live:* `{execution.get('ready_for_live', '-')}`\n"
        f"*Decision:* `{execution.get('decision', '-')}`\n"
        f"*Blocking Count:* `{execution.get('blocking_count', '-')}`\n\n"
        "*Operator*\n"
        f"*BOT Can Move:* `{operator.get('can_bot_trade', '-')}`\n"
        f"*Human Action Required:* `{operator.get('human_action_required', '-')}`\n"
        f"*Execution Mode:* `{operator.get('execution_mode', '-')}`\n"
        f"*Operator Mode:* `{operator.get('operator_mode', '-')}`\n"
        f"*Mode Badge:* `{mode_badge.get('label', '-')}`\n\n"
        "*Gate Stack*\n"
        f"*Data Gate:* `{gate_stack.get('data_gate', '-')}`\n"
        f"*Resolver Gate:* `{gate_stack.get('resolver_gate', '-')}`\n"
        f"*Probability Gate:* `{gate_stack.get('probability_gate', '-')}`\n"
        f"*Freshness Gate:* `{gate_stack.get('freshness_gate', '-')}`\n"
        f"*Authorization Gate:* `{gate_stack.get('authorization_gate', '-')}`\n"
        f"*Execution Gate:* `{gate_stack.get('execution_gate', '-')}`\n\n"
        f"*Block Reasons:* `{block_reasons}`"
    )


def _extract_promotion_state(*payloads: dict | None) -> dict:
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        candidate = payload.get("promotion_state")
        if isinstance(candidate, dict):
            return candidate
        nested_probability = payload.get("probability")
        if isinstance(nested_probability, dict):
            candidate = nested_probability.get("promotion_state")
            if isinstance(candidate, dict):
                return candidate
        nested_validation = payload.get("validation")
        if isinstance(nested_validation, dict):
            candidate = nested_validation.get("promotion_state")
            if isinstance(candidate, dict):
                return candidate
    return {}
