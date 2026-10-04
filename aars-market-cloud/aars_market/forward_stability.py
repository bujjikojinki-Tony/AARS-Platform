from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence

from .trial import _risk_score


EXECUTION_MODE = "PAPER_ONLY"
STABILITY_SCHEMA_VERSION = "mil3.forward-stability.v1"


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse(value: str) -> datetime:
    return _utc(datetime.fromisoformat(value))


@dataclass(frozen=True)
class ForwardStabilityPolicy:
    evaluation_checkpoints: int = 30
    minimum_forward_bars: int = 720
    minimum_consecutive_qualifying: int = 3
    maximum_checkpoint_gap_hours: float = 48.0
    edge_decay_score: float = 0.25
    liquidation_risk_rise: float = 0.02

    def __post_init__(self) -> None:
        if self.evaluation_checkpoints <= 0:
            raise ValueError("evaluation checkpoints must be positive")
        if self.minimum_forward_bars <= 0:
            raise ValueError("minimum forward bars must be positive")
        if self.minimum_consecutive_qualifying <= 0:
            raise ValueError("consecutive qualifying threshold must be positive")
        if self.minimum_consecutive_qualifying > self.evaluation_checkpoints:
            raise ValueError("qualifying threshold must fit evaluation window")
        if self.maximum_checkpoint_gap_hours <= 0:
            raise ValueError("checkpoint gap must be positive")
        if self.edge_decay_score < 0 or self.liquidation_risk_rise < 0:
            raise ValueError("decay and risk-rise thresholds must be non-negative")


def _point(observation_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    results = payload["results"]
    baseline = results["baseline"]
    proposed = results["proposed"]
    score_delta = _risk_score(proposed) - _risk_score(baseline)
    return {
        "observation_id": observation_id,
        "observed_through": payload["boundary"]["synchronized_forward_end"],
        "forward_bars": int(results["forward_bars"]),
        "input_sha256": payload["input_evidence"]["combined_sha256"],
        "previous_observation_id": payload["lineage"]["previous_observation_id"],
        "previous_input_sha256": payload["lineage"]["previous_input_sha256"],
        "disposition": payload["review_gate"]["disposition"],
        "stop_triggered": payload["stop_condition"]["triggered"],
        "stop_reasons": list(payload["stop_condition"]["reasons"]),
        "score_delta": score_delta,
        "return_delta": float(
            results["delta_proposed_minus_baseline"]["mean_total_return"]
        ),
        "drawdown_delta": float(
            results["delta_proposed_minus_baseline"]["worst_max_drawdown"]
        ),
        "proposed_max_liquidation_risk": float(
            proposed["max_liquidation_risk"]
        ),
        "proposed_liquidation_events": int(proposed["liquidation_events"]),
    }


def _alarm(
    code: str,
    severity: str,
    trigger: str,
    impact: str,
    recommended_action: str,
    closure_condition: str,
) -> dict[str, str]:
    return {
        "code": code,
        "severity": severity,
        "object": "FORWARD_PAPER_OBSERVATION",
        "trigger": trigger,
        "impact": impact,
        "recommended_action": recommended_action,
        "closure_condition": closure_condition,
    }


def build_forward_stability(
    observations: Sequence[tuple[str, dict[str, Any]]],
    *,
    policy: ForwardStabilityPolicy = ForwardStabilityPolicy(),
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """Derive advisory persistence and decay evidence from immutable checkpoints."""
    if any(item.get("schema_version") != "mil3.forward-observation.v1" for _, item in observations):
        raise ValueError("unsupported forward observation schema")
    if any(item.get("execution_mode") != EXECUTION_MODE for _, item in observations):
        raise ValueError("forward stability requires PAPER_ONLY evidence")
    if any(not item.get("trial_id") or not item.get("target_strategy") for _, item in observations):
        raise ValueError("forward observation trial and target are required")
    trial_ids = {str(item["trial_id"]) for _, item in observations}
    targets = {str(item["target_strategy"]) for _, item in observations}
    if len(trial_ids) > 1 or len(targets) > 1:
        raise ValueError("forward stability requires one trial and target strategy")
    for _, item in observations:
        for authority in (item.get("authority", {}), item.get("review_gate", {})):
            if any(authority.get(key) is not False for key in (
                "observation_application_allowed",
                "automatic_strategy_change_allowed",
                "live_execution_allowed",
            )):
                raise ValueError("forward observation exceeds stability authority")

    selected = list(observations[-policy.evaluation_checkpoints :])
    points = [_point(observation_id, payload) for observation_id, payload in selected]
    transitions: list[dict[str, Any]] = []
    chain_broken = bool(
        points
        and len(observations) <= policy.evaluation_checkpoints
        and (
            points[0]["previous_observation_id"] is not None
            or points[0]["previous_input_sha256"] is not None
        )
    )
    gap_exceeded = False
    for before, after in zip(points, points[1:]):
        gap_hours = (
            _parse(after["observed_through"]) - _parse(before["observed_through"])
        ).total_seconds() / 3600.0
        linked = (
            after["previous_observation_id"] == before["observation_id"]
            and after["previous_input_sha256"] == before["input_sha256"]
        )
        chain_broken = chain_broken or not linked or gap_hours <= 0
        gap_exceeded = gap_exceeded or gap_hours > policy.maximum_checkpoint_gap_hours
        transitions.append({
            "from_observation_id": before["observation_id"],
            "to_observation_id": after["observation_id"],
            "gap_hours": gap_hours,
            "lineage_verified": linked,
            "score_delta_change": after["score_delta"] - before["score_delta"],
            "return_delta_change": after["return_delta"] - before["return_delta"],
            "liquidation_risk_change": (
                after["proposed_max_liquidation_risk"]
                - before["proposed_max_liquidation_risk"]
            ),
        })

    best_score = max((point["score_delta"] for point in points), default=0.0)
    latest = points[-1] if points else None
    current_score = latest["score_delta"] if latest else None
    decay = bool(
        latest
        and best_score > 0
        and best_score - latest["score_delta"] >= policy.edge_decay_score
    )
    reversal = bool(
        latest
        and latest["score_delta"] < 0
        and any(point["score_delta"] >= 0 for point in points[:-1])
    )
    risk_rising = bool(
        len(points) >= 3
        and points[-3]["proposed_max_liquidation_risk"]
        < points[-2]["proposed_max_liquidation_risk"]
        < points[-1]["proposed_max_liquidation_risk"]
        and points[-1]["proposed_max_liquidation_risk"]
        - points[-3]["proposed_max_liquidation_risk"]
        >= policy.liquidation_risk_rise
    )

    def qualifies(point: dict[str, Any]) -> bool:
        return bool(
            point["forward_bars"] >= policy.minimum_forward_bars
            and not point["stop_triggered"]
            and point["score_delta"] >= 0
            and point["return_delta"] >= 0
            and point["proposed_liquidation_events"] == 0
        )

    consecutive = 0
    for point in reversed(points):
        if qualifies(point):
            consecutive += 1
        else:
            break
    warnings: list[str] = []
    alarms: list[dict[str, str]] = []
    if not latest or latest["forward_bars"] < policy.minimum_forward_bars:
        warnings.append("INSUFFICIENT_OBSERVATION_HORIZON")
    if chain_broken:
        warnings.append("CHECKPOINT_LINEAGE_BROKEN")
        alarms.append(_alarm(
            "CHECKPOINT_LINEAGE_BROKEN", "HIGH",
            "A checkpoint does not reference the immediately previous observation and input hash.",
            "The evidence sequence cannot support persistence claims.",
            "Stop review and inspect the immutable archive for missing or altered checkpoints.",
            "Every transition in the evaluation window verifies its predecessor ID and input hash.",
        ))
    if gap_exceeded:
        warnings.append("CHECKPOINT_CADENCE_GAP")
        alarms.append(_alarm(
            "CHECKPOINT_CADENCE_GAP", "MEDIUM",
            f"At least one checkpoint gap exceeds {policy.maximum_checkpoint_gap_hours:g} hours.",
            "Market regimes may have changed without intermediate observation evidence.",
            "Restore scheduled checkpoint generation and accumulate a continuous window.",
            "All evaluated gaps are within the configured cadence limit.",
        ))
    if decay:
        warnings.append("PROPOSED_EDGE_DECAY")
        alarms.append(_alarm(
            "PROPOSED_EDGE_DECAY", "MEDIUM",
            f"Current score advantage is at least {policy.edge_decay_score:g} below its observed peak.",
            "The proposed configuration's earlier advantage is weakening.",
            "Continue baseline and investigate regime, costs and exposure before any further review.",
            "The score advantage recovers within the configured decay tolerance.",
        ))
    if reversal:
        warnings.append("PROPOSED_EDGE_REVERSAL")
        alarms.append(_alarm(
            "PROPOSED_EDGE_REVERSAL", "HIGH",
            "The latest proposed-minus-baseline risk-adjusted score is negative after a non-negative checkpoint.",
            "The proposed configuration no longer dominates the baseline in current evidence.",
            "Keep baseline; continue observation only after reviewing the reversal evidence.",
            "A new uninterrupted qualifying sequence satisfies the full confirmation policy.",
        ))
    if risk_rising:
        warnings.append("LIQUIDATION_RISK_RISING")
        alarms.append(_alarm(
            "LIQUIDATION_RISK_RISING", "HIGH",
            "Liquidation-risk approximation rose across three checkpoints beyond policy tolerance.",
            "Risk is deteriorating even without a hard stop breach.",
            "Keep baseline and inspect leverage, margin buffer and funding conditions.",
            "Risk stops rising and a new qualifying checkpoint sequence is established.",
        ))
    if latest and latest["stop_triggered"]:
        warnings.append("FORWARD_STOP_TRIGGERED")
        alarms.append(_alarm(
            "FORWARD_STOP_TRIGGERED", "CRITICAL",
            "The latest immutable checkpoint triggered a configured paper stop.",
            "Extended observation is no longer eligible for confirmation.",
            "Stop the monitor for this trial and retain the baseline configuration.",
            "A new governed proposal and trial lifecycle is completed; this trial remains stopped.",
        ))

    blocking = {"CHECKPOINT_LINEAGE_BROKEN", "CHECKPOINT_CADENCE_GAP"}
    if latest and latest["stop_triggered"]:
        disposition = "STOP_EXTENDED_OBSERVATION"
    elif any(code in blocking for code in warnings):
        disposition = "DEFER_EXTENDED_OBSERVATION"
    elif (
        consecutive >= policy.minimum_consecutive_qualifying
        and not any(code in warnings for code in (
            "PROPOSED_EDGE_DECAY",
            "PROPOSED_EDGE_REVERSAL",
            "LIQUIDATION_RISK_RISING",
        ))
    ):
        disposition = "EXTENDED_OBSERVATION_CONFIRMED"
    else:
        disposition = "CONTINUE_EXTENDED_OBSERVATION"

    generated = _utc(generated_at or datetime.now(timezone.utc))
    return {
        "schema_version": STABILITY_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "generated_at": generated.isoformat(),
        "trial_id": next(iter(trial_ids), None),
        "target_strategy": next(iter(targets), None),
        "policy": asdict(policy),
        "points": points,
        "transitions": transitions,
        "summary": {
            "available_checkpoints": len(observations),
            "evaluated_checkpoints": len(points),
            "latest_forward_bars": latest["forward_bars"] if latest else 0,
            "consecutive_qualifying_checkpoints": consecutive,
            "best_score_delta": best_score if points else None,
            "current_score_delta": current_score,
            "current_return_delta": latest["return_delta"] if latest else None,
            "current_liquidation_risk": (
                latest["proposed_max_liquidation_risk"] if latest else None
            ),
            "warning_codes": warnings,
        },
        "alarms": alarms,
        "review_gate": {
            "disposition": disposition,
            "next_review_condition": (
                "Start a new governed proposal/trial lifecycle."
                if disposition == "STOP_EXTENDED_OBSERVATION"
                else (
                    "Repair checkpoint continuity before review."
                    if disposition == "DEFER_EXTENDED_OBSERVATION"
                    else (
                        "Policy evidence is confirmed for human paper review only."
                        if disposition == "EXTENDED_OBSERVATION_CONFIRMED"
                        else (
                            f"Reach {policy.minimum_forward_bars} forward bars and "
                            f"{policy.minimum_consecutive_qualifying} consecutive qualifying checkpoints."
                        )
                    )
                )
            ),
            "observation_application_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        },
        "authority": {
            "observation_application_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        },
    }
