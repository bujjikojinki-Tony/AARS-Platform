from aars_weather_trading.gates.freshness_gate import evaluate_freshness_gate
from aars_weather_trading.gates.probability_gate import evaluate_probability_gate
from weather_execution_gateway.models.order_intent import (
    EXECUTION_INTENT_SCHEMA_VERSION,
    OrderIntent,
)
from weather_execution_gateway.models.risk_state import RiskState
from weather_execution_gateway.risk.exposure_limits import ExposureLimits
from weather_execution_gateway.risk.kill_switch import KillSwitch


class RiskGateEngine:
    def __init__(
        self,
        whitelist_markets: set[str],
        execution_enabled: bool,
        kill_switch: KillSwitch,
        exposure_limits: ExposureLimits,
    ) -> None:
        self.whitelist_markets = whitelist_markets
        self.execution_enabled = execution_enabled
        self.kill_switch = kill_switch
        self.exposure_limits = exposure_limits

    def evaluate(
        self,
        intent: OrderIntent,
        market_notional: float = 0.0,
        total_notional: float = 0.0,
        approval_valid: bool = False,
        unified_status: dict | None = None,
    ) -> RiskState:
        if self.kill_switch.is_active():
            new_order_notional = intent.price * intent.size
            return RiskState(
                market_allowed=False,
                approval_present=approval_valid,
                kill_switch_active=True,
                notional_allowed=False,
                execution_enabled=self.execution_enabled,
                market_notional=market_notional,
                total_notional=total_notional,
                new_order_notional=new_order_notional,
                reason="kill_switch_active",
            )

        if intent.market_id not in self.whitelist_markets:
            new_order_notional = intent.price * intent.size
            return RiskState(
                market_allowed=False,
                approval_present=approval_valid,
                kill_switch_active=False,
                notional_allowed=False,
                execution_enabled=self.execution_enabled,
                market_notional=market_notional,
                total_notional=total_notional,
                new_order_notional=new_order_notional,
                reason="market_not_whitelisted",
            )

        contract_reason = _execution_intent_contract_block_reason(intent)
        if contract_reason is not None:
            new_order_notional = intent.price * intent.size
            return RiskState(
                market_allowed=True,
                approval_present=approval_valid,
                kill_switch_active=False,
                notional_allowed=False,
                execution_enabled=self.execution_enabled,
                market_notional=market_notional,
                total_notional=total_notional,
                new_order_notional=new_order_notional,
                reason=contract_reason,
            )

        gate_stack_reason = _unified_gate_stack_block_reason(unified_status)
        if gate_stack_reason is not None:
            new_order_notional = intent.price * intent.size
            return RiskState(
                market_allowed=True,
                approval_present=approval_valid,
                kill_switch_active=False,
                notional_allowed=False,
                execution_enabled=self.execution_enabled,
                market_notional=market_notional,
                total_notional=total_notional,
                new_order_notional=new_order_notional,
                reason=gate_stack_reason,
            )

        if _gate_source(unified_status) != "api":
            freshness_result = evaluate_freshness_gate(unified_status)
            if not freshness_result.passed:
                new_order_notional = intent.price * intent.size
                return RiskState(
                    market_allowed=True,
                    approval_present=approval_valid,
                    kill_switch_active=False,
                    notional_allowed=False,
                    execution_enabled=self.execution_enabled,
                    market_notional=market_notional,
                    total_notional=total_notional,
                    new_order_notional=new_order_notional,
                    reason=freshness_result.block_reasons[0],
                )

        if not approval_valid:
            new_order_notional = intent.price * intent.size
            return RiskState(
                market_allowed=True,
                approval_present=False,
                kill_switch_active=False,
                notional_allowed=False,
                execution_enabled=self.execution_enabled,
                market_notional=market_notional,
                total_notional=total_notional,
                new_order_notional=new_order_notional,
                reason="approval_invalid_or_expired",
            )

        new_order_notional = intent.price * intent.size
        notional_allowed = self.exposure_limits.allows(
            market_notional=market_notional,
            total_notional=total_notional,
            new_order_notional=new_order_notional,
        )

        if not notional_allowed:
            return RiskState(
                market_allowed=True,
                approval_present=True,
                kill_switch_active=False,
                notional_allowed=False,
                execution_enabled=self.execution_enabled,
                market_notional=market_notional,
                total_notional=total_notional,
                new_order_notional=new_order_notional,
                reason="exposure_limit_exceeded",
            )

        if self.execution_enabled and not _probability_contract_allows_live(intent):
            return RiskState(
                market_allowed=True,
                approval_present=True,
                kill_switch_active=False,
                notional_allowed=True,
                execution_enabled=self.execution_enabled,
                market_notional=market_notional,
                total_notional=total_notional,
                new_order_notional=new_order_notional,
                reason="probability_contract_blocks_live_execution",
            )

        if not self.execution_enabled:
            return RiskState(
                market_allowed=True,
                approval_present=True,
                kill_switch_active=False,
                notional_allowed=True,
                execution_enabled=False,
                market_notional=market_notional,
                total_notional=total_notional,
                new_order_notional=new_order_notional,
                reason="execution_disabled_dry_run_only",
            )

        return RiskState(
            market_allowed=True,
            approval_present=True,
            kill_switch_active=False,
            notional_allowed=True,
            execution_enabled=True,
            market_notional=market_notional,
            total_notional=total_notional,
            new_order_notional=new_order_notional,
            reason=None,
        )


def _probability_contract_allows_live(intent: OrderIntent) -> bool:
    contract = intent.probability_contract or {}
    probability_mode = str(contract.get("probability_mode") or intent.probability_mode or "")
    execution_constraint = str(
        contract.get("execution_constraint")
        or intent.execution_constraint
        or ""
    )
    calibration_status = str(contract.get("calibration_status") or intent.calibration_status or "")
    probability_result = evaluate_probability_gate(probability_mode)
    return (
        probability_result.passed
        and execution_constraint == "live_execution_allowed"
        and calibration_status == "calibrated"
    )


def _execution_intent_contract_block_reason(intent: OrderIntent) -> str | None:
    if str(intent.schema_version or "") != EXECUTION_INTENT_SCHEMA_VERSION:
        return "execution_intent_contract_invalid"
    if not str(intent.decision_ref or "").strip():
        return "execution_intent_contract_invalid"
    if not str(intent.authorization_ref or "").strip():
        return "execution_intent_contract_invalid"
    return None


def _unified_gate_stack_block_reason(unified_status: dict | None) -> str | None:
    if not isinstance(unified_status, dict):
        return None
    gate_stack = unified_status.get("gate_stack")
    if not isinstance(gate_stack, dict):
        return None

    gate_priority = [
        "authorization_gate",
        "execution_gate",
        "freshness_gate",
        "resolver_gate",
        "probability_gate",
        "data_gate",
    ]
    for gate_name in gate_priority:
        if str(gate_stack.get(gate_name) or "").lower() != "blocked":
            continue
        reasons_key = f"{gate_name}_reasons"
        reasons = gate_stack.get(reasons_key) or gate_stack.get("block_reasons") or []
        if isinstance(reasons, list) and reasons:
            return str(reasons[0])
        return "unified_gate_stack_blocked"
    return None


def _gate_source(unified_status: dict | None) -> str:
    if not isinstance(unified_status, dict):
        return ""
    contracts = unified_status.get("contracts")
    if not isinstance(contracts, dict):
        return str(unified_status.get("gate_source") or "").strip().lower()
    return str(contracts.get("gate_source") or unified_status.get("gate_source") or "").strip().lower()
