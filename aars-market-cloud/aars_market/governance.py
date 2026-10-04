from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from statistics import fmean
from typing import Any, Sequence


EXECUTION_MODE = "PAPER_ONLY"
GOVERNANCE_SCHEMA_VERSION = "mil3.promotion-governance.v1"
HIGH_RISK_WARNING_CODES = frozenset(
    {
        "BASELINE_UNDERPERFORMANCE",
        "FUNDING_HISTORY_FALLBACK",
        "INSUFFICIENT_FOLDS",
        "LIQUIDATION_APPROXIMATION_BREACH",
        "TRAIN_TEST_SCORE_DECAY",
    }
)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class PromotionPolicy:
    evaluation_window_snapshots: int = 30
    min_snapshots: int = 30
    min_consecutive_ready: int = 7
    max_parameter_change_rate: float = 0.10
    min_mean_selection_stability: float = 0.70
    min_mean_excess_return_vs_buy_hold: float = 0.0
    max_portfolio_drawdown: float = 0.20
    max_liquidation_risk: float = 0.10
    max_high_risk_warning_recurrence: float = 0.10
    reject_excess_return_below: float = -0.05
    reject_drawdown_at_or_above: float = 0.35
    reject_liquidation_risk_at_or_above: float = 0.25

    def __post_init__(self) -> None:
        if self.evaluation_window_snapshots <= 0 or self.min_snapshots <= 0:
            raise ValueError("governance snapshot thresholds must be positive")
        if self.min_consecutive_ready <= 0:
            raise ValueError("min_consecutive_ready must be positive")
        if self.evaluation_window_snapshots < self.min_snapshots:
            raise ValueError("evaluation window must contain the minimum snapshot history")
        if self.min_consecutive_ready > self.evaluation_window_snapshots:
            raise ValueError("consecutive ready threshold must fit the evaluation window")
        bounded = (
            self.max_parameter_change_rate,
            self.min_mean_selection_stability,
            self.max_portfolio_drawdown,
            self.max_liquidation_risk,
            self.max_high_risk_warning_recurrence,
            self.reject_drawdown_at_or_above,
            self.reject_liquidation_risk_at_or_above,
        )
        if any(value < 0 or value > 1 for value in bounded):
            raise ValueError("governance rates must be between zero and one")
        if self.reject_drawdown_at_or_above < self.max_portfolio_drawdown:
            raise ValueError("reject drawdown must not be below candidate drawdown")
        if self.reject_liquidation_risk_at_or_above < self.max_liquidation_risk:
            raise ValueError("reject liquidation risk must not be below candidate risk")
        if self.reject_excess_return_below > self.min_mean_excess_return_vs_buy_hold:
            raise ValueError("reject excess return must not exceed candidate threshold")


def _check(
    check_id: str,
    label: str,
    status: str,
    observed: Any,
    requirement: str,
    impact: str,
    recovery_condition: str,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "label": label,
        "status": status,
        "observed": observed,
        "requirement": requirement,
        "impact": impact,
        "recovery_condition": recovery_condition,
    }


def _threshold_status(
    observed: float,
    *,
    candidate: float,
    reject: float,
    higher_is_better: bool,
) -> str:
    if higher_is_better:
        if observed >= candidate:
            return "PASS"
        return "REJECT" if observed <= reject else "BLOCK"
    if observed <= candidate:
        return "PASS"
    return "REJECT" if observed >= reject else "BLOCK"


def build_promotion_governance(
    stability: dict[str, Any],
    *,
    policy: PromotionPolicy = PromotionPolicy(),
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """Evaluate immutable shadow evidence without mutating strategy state."""
    if stability.get("schema_version") != "mil3.shadow-stability.v1":
        raise ValueError("unsupported shadow stability schema")
    if stability.get("execution_mode") != EXECUTION_MODE:
        raise ValueError("promotion governance requires PAPER_ONLY evidence")
    if stability.get("review_gate", {}).get("live_execution_allowed") is not False:
        raise ValueError("stability evidence must explicitly disallow live execution")

    archived_points: Sequence[dict[str, Any]] = stability.get("points", [])
    all_points: Sequence[dict[str, Any]] = stability.get(
        "promotion_eligible_points", archived_points
    )
    points = list(all_points[-policy.evaluation_window_snapshots :])
    latest = points[-1] if points else None
    transition_count = max(0, len(points) - 1)
    change_events = sum(
        before.get("selected_candidates") != after.get("selected_candidates")
        for before, after in zip(points, points[1:])
    ) if transition_count else 0
    parameter_change_rate = change_events / transition_count if transition_count else 0.0
    mean_selection_stability = (
        fmean(float(item["mean_selection_stability"]) for item in points)
        if points
        else 0.0
    )
    mean_excess_return = (
        fmean(
            float(item.get("mean_validation_excess_return_vs_buy_hold", 0.0))
            for item in points
        )
        if points
        else 0.0
    )
    max_drawdown = max(
        (float(item["portfolio"]["max_drawdown"]) for item in points), default=0.0
    )
    max_liquidation_risk = max(
        (float(item["portfolio"]["max_liquidation_risk"]) for item in points),
        default=0.0,
    )
    max_liquidation_events = max(
        (int(item["portfolio"]["liquidation_events"]) for item in points), default=0
    )
    warning_counts: Counter[str] = Counter(
        code for item in points for code in item.get("warning_codes", [])
    )
    high_warning_recurrence = {
        code: count / len(points)
        for code, count in sorted(warning_counts.items())
        if code in HIGH_RISK_WARNING_CODES and points
    }
    max_warning_recurrence = max(high_warning_recurrence.values(), default=0.0)
    latest_ready = bool(
        latest and latest["review_disposition"] == "READY_FOR_SHADOW_REVIEW"
    )
    latest_healthy = bool(latest and not latest["portfolio"]["degraded"])
    consecutive_ready = 0
    for point in points:
        if point["review_disposition"] == "READY_FOR_SHADOW_REVIEW":
            consecutive_ready += 1
        else:
            consecutive_ready = 0

    checks = [
        _check(
            "MINIMUM_DAILY_HISTORY",
            "Minimum immutable daily history",
            "PASS" if len(all_points) >= policy.min_snapshots else "BLOCK",
            len(all_points),
            f">= {policy.min_snapshots} snapshots",
            "Short histories cannot demonstrate persistence across market conditions.",
            f"Archive {max(0, policy.min_snapshots - len(all_points))} more distinct daily snapshots.",
        ),
        _check(
            "CONSECUTIVE_READY_REVIEWS",
            "Consecutive ready review gates",
            "PASS" if consecutive_ready >= policy.min_consecutive_ready else "BLOCK",
            consecutive_ready,
            f">= {policy.min_consecutive_ready}",
            "Recent evidence has not remained continuously reviewable.",
            "Resolve deferral causes and accumulate an uninterrupted ready sequence.",
        ),
        _check(
            "CURRENT_REVIEW_GATE",
            "Latest review gate",
            "PASS" if latest_ready else "BLOCK",
            latest["review_disposition"] if latest else None,
            "READY_FOR_SHADOW_REVIEW",
            "A deferred latest snapshot cannot support promotion review.",
            "Resolve the latest snapshot reasons and archive a ready daily result.",
        ),
        _check(
            "LATEST_PORTFOLIO_HEALTH",
            "Latest portfolio evidence health",
            "PASS" if latest_healthy else "BLOCK",
            "HEALTHY" if latest_healthy else "DEGRADED_OR_MISSING",
            "HEALTHY",
            "Stale, incomplete, or degraded portfolio evidence is not promotable.",
            "Restore candle/funding coverage and archive a non-degraded portfolio result.",
        ),
        _check(
            "PARAMETER_CHANGE_RATE",
            "Parameter change rate",
            "PASS" if points and parameter_change_rate <= policy.max_parameter_change_rate else "BLOCK",
            parameter_change_rate if points else None,
            f"<= {policy.max_parameter_change_rate}",
            "Frequent candidate changes indicate unstable selection.",
            "Continue observation until changes fall below the policy rate.",
        ),
        _check(
            "MEAN_SELECTION_STABILITY",
            "Mean parameter-selection stability",
            "PASS" if mean_selection_stability >= policy.min_mean_selection_stability else "BLOCK",
            mean_selection_stability,
            f">= {policy.min_mean_selection_stability}",
            "Low fold agreement weakens confidence in the selected configuration.",
            "Collect additional folds or simplify the bounded candidate grid.",
        ),
        _check(
            "EXCESS_RETURN_VS_BUY_HOLD",
            "Mean out-of-sample excess return vs Buy & Hold",
            _threshold_status(
                mean_excess_return,
                candidate=policy.min_mean_excess_return_vs_buy_hold,
                reject=policy.reject_excess_return_below,
                higher_is_better=True,
            ) if points else "BLOCK",
            mean_excess_return if points else None,
            f">= {policy.min_mean_excess_return_vs_buy_hold}",
            "The strategy has not justified its added complexity against the baseline.",
            "Accumulate out-of-sample evidence at or above Buy & Hold after modeled costs.",
        ),
        _check(
            "MAX_PORTFOLIO_DRAWDOWN",
            "Maximum portfolio drawdown",
            _threshold_status(
                max_drawdown,
                candidate=policy.max_portfolio_drawdown,
                reject=policy.reject_drawdown_at_or_above,
                higher_is_better=False,
            ) if points else "BLOCK",
            max_drawdown if points else None,
            f"<= {policy.max_portfolio_drawdown}",
            "Excessive drawdown violates the promotion risk budget.",
            "Reduce exposure or reject the configuration until drawdown is within policy.",
        ),
        _check(
            "MAX_LIQUIDATION_RISK",
            "Maximum liquidation-risk approximation",
            _threshold_status(
                max_liquidation_risk,
                candidate=policy.max_liquidation_risk,
                reject=policy.reject_liquidation_risk_at_or_above,
                higher_is_better=False,
            ) if points else "BLOCK",
            max_liquidation_risk if points else None,
            f"<= {policy.max_liquidation_risk}",
            "Material liquidation proximity is incompatible with promotion review.",
            "Reduce leverage/inventory until the approximation remains within policy.",
        ),
        _check(
            "LIQUIDATION_EVENTS",
            "Liquidation approximation breaches",
            "PASS" if points and max_liquidation_events == 0 else ("REJECT" if max_liquidation_events else "BLOCK"),
            max_liquidation_events if points else None,
            "= 0",
            "Any approximation breach makes the configuration non-viable for promotion.",
            "Reject or materially redesign the leveraged configuration, then restart observation.",
        ),
        _check(
            "HIGH_RISK_WARNING_RECURRENCE",
            "High-risk warning recurrence",
            "PASS" if points and max_warning_recurrence <= policy.max_high_risk_warning_recurrence else "BLOCK",
            {
                "maximum": max_warning_recurrence,
                "by_code": high_warning_recurrence,
            },
            f"maximum per-code recurrence <= {policy.max_high_risk_warning_recurrence}",
            "Recurring high-risk warnings show unresolved evidence-quality or performance problems.",
            "Resolve the warning cause and accumulate clean daily snapshots.",
        ),
    ]

    rejected = [item["id"] for item in checks if item["status"] == "REJECT"]
    blocked = [item["id"] for item in checks if item["status"] == "BLOCK"]
    if rejected:
        disposition = "REJECT_PROMOTION"
        next_review = "Material risk/performance evidence must be redesigned before a new observation cycle."
    elif blocked:
        disposition = "CONTINUE_OBSERVATION"
        next_review = "Re-evaluate after every new immutable daily snapshot and all blocking checks pass."
    else:
        disposition = "PROMOTION_CANDIDATE"
        next_review = "Human review may consider a separately governed paper-only configuration change."

    generated = _utc(generated_at or datetime.now(timezone.utc))
    return {
        "schema_version": GOVERNANCE_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "generated_at": generated.isoformat(),
        "target_strategy": latest["validation_strategy"] if latest else None,
        "evidence_window": {
            "available_snapshots": len(all_points),
            "archived_snapshots": len(archived_points),
            "excluded_ineligible_snapshots": len(archived_points) - len(all_points),
            "evaluated_snapshots": len(points),
            "first_as_of": points[0]["as_of"] if points else None,
            "latest_as_of": points[-1]["as_of"] if points else None,
        },
        "policy": asdict(policy),
        "observed": {
            "parameter_change_rate": parameter_change_rate,
            "mean_selection_stability": mean_selection_stability,
            "mean_excess_return_vs_buy_hold": mean_excess_return if points else None,
            "max_portfolio_drawdown": max_drawdown if points else None,
            "max_liquidation_risk": max_liquidation_risk if points else None,
            "max_liquidation_events": max_liquidation_events if points else None,
            "high_risk_warning_recurrence": high_warning_recurrence,
        },
        "checks": checks,
        "decision": {
            "disposition": disposition,
            "blocking_checks": blocked,
            "rejection_checks": rejected,
            "next_review_condition": next_review,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        },
        "review_gate": {
            "disposition": disposition,
            "live_execution_allowed": False,
        },
    }
