from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Sequence

from .diagnostics import _select_snapshot, _utc, build_strategy_diagnostics
from .robustness import (
    RobustnessSettings,
    build_frozen_challenger_robustness,
    frozen_specification,
)
from .runtime_ledger import latest_synchronized_closed_boundary, timeframe_duration
from .storage import MarketStore


SCHEMA_VERSION = "mil3.frozen-forward-evidence-monitor.v1"
CHECKPOINT_SCHEMA_VERSION = "mil3.frozen-forward-evidence-checkpoint.v1"
EXECUTION_MODE = "PAPER_ONLY"


@dataclass(frozen=True)
class FrozenMonitorSettings:
    robustness: RobustnessSettings = RobustnessSettings()
    max_new_checkpoints_per_cycle: int = 8
    state_mix_shift_limit: float = 0.20
    state_outcome_deterioration_per_bar: float = 0.00005
    cost_return_deterioration_limit: float = 0.05
    latest_fold_loss_limit: float = 0.05

    def __post_init__(self) -> None:
        if self.max_new_checkpoints_per_cycle <= 0:
            raise ValueError("max_new_checkpoints_per_cycle must be positive")
        for name in (
            "state_mix_shift_limit",
            "state_outcome_deterioration_per_bar",
            "cost_return_deterioration_limit",
            "latest_fold_loss_limit",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")


def _authority() -> dict[str, bool]:
    return {
        "read_only": True,
        "parameter_tuning_allowed": False,
        "proposal_creation_allowed": False,
        "challenger_activation_allowed": False,
        "automatic_strategy_change_allowed": False,
        "live_execution_allowed": False,
    }


def _alert(
    code: str,
    severity: str,
    trigger: str,
    impact: str,
    evidence: Any,
    recommended_response: str,
    closure_condition: str,
) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "trigger": trigger,
        "impact": impact,
        "evidence": evidence,
        "recommended_response": recommended_response,
        "closure_condition": closure_condition,
    }


def _degraded(reason: str, snapshot_id: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "status": "DEGRADED",
        "data_trust": {
            "status": "UNAVAILABLE",
            "reason": reason,
            "source_snapshot_id": snapshot_id,
        },
        "authority": _authority(),
        "frozen_specification": None,
        "collection": None,
        "drift": {"status": "UNKNOWN", "alerts": []},
        "latest_robustness_gate": None,
        "review_gate": {
            "disposition": "DEFER",
            "blocking_reasons": [reason],
            "parameter_tuning_allowed": False,
            "proposal_creation_allowed": False,
            "challenger_activation_allowed": False,
            "live_execution_allowed": False,
        },
    }


def _source(
    store: MarketStore,
    snapshot_id: str | None,
) -> tuple[dict[str, Any], str, dict[str, Any]] | dict[str, Any]:
    diagnostic = build_strategy_diagnostics(store, snapshot_id=snapshot_id)
    if diagnostic["status"] != "READY":
        return _degraded(
            f"SOURCE_DIAGNOSTIC_{diagnostic['data_trust']['reason']}",
            diagnostic["data_trust"].get("source_snapshot_id") or snapshot_id,
        )
    source_id = str(diagnostic["data_trust"]["source_snapshot_id"])
    selected = _select_snapshot(store, source_id)
    if selected is None:
        return _degraded("SOURCE_SNAPSHOT_NOT_FOUND", source_id)
    return diagnostic, source_id, selected[1]


def _fold_schedule(
    store: MarketStore,
    snapshot: Mapping[str, Any],
    *,
    settings: RobustnessSettings,
    observed_at: datetime,
) -> dict[str, Any]:
    symbols = tuple(str(item) for item in snapshot["symbols"])
    timeframe = str(snapshot["configuration"]["timeframe"])
    frozen_at = _utc(snapshot["as_of"])
    current_boundary, per_asset = latest_synchronized_closed_boundary(
        store, symbols, timeframe, observed_at=observed_at
    )
    if current_boundary is None or current_boundary < frozen_at:
        raise ValueError("SYNCHRONIZED_VALIDATION_BOUNDARY_UNAVAILABLE")
    candles_by_symbol = {
        symbol: store.load_candles(symbol, timeframe, end=current_boundary)
        for symbol in symbols
    }
    lengths = {len(rows) for rows in candles_by_symbol.values()}
    if len(lengths) != 1 or not lengths or next(iter(lengths)) <= settings.warmup_bars:
        raise ValueError("UNALIGNED_VALIDATION_HISTORY")
    reference = tuple(
        candle.open_time for candle in next(iter(candles_by_symbol.values()))
    )
    if any(
        tuple(candle.open_time for candle in rows) != reference
        for rows in candles_by_symbol.values()
    ):
        raise ValueError("UNALIGNED_VALIDATION_HISTORY")
    interval = timeframe_duration(timeframe)
    if any(right - left != interval for left, right in zip(reference, reference[1:])):
        raise ValueError("VALIDATION_HISTORY_GAP")

    completed: list[datetime] = []
    first_at = reference[0]
    test_start = settings.warmup_bars - 1
    while True:
        test_end = test_start + settings.test_bars
        start_at = first_at + interval * test_start
        end_at = first_at + interval * (test_end - 1)
        if start_at > frozen_at:
            if test_end <= len(reference):
                completed.append(end_at)
            else:
                next_boundary = end_at
                break
        test_start += settings.step_bars
    return {
        "current_boundary": current_boundary,
        "per_asset_boundary": per_asset,
        "post_freeze_boundaries": tuple(completed),
        "next_boundary": next_boundary,
        "timeframe": timeframe,
        "interval": interval,
    }


def _report_sha256(report: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        report, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _checkpoint_payload(
    report: dict[str, Any],
    *,
    fold_count: int,
    created_at: datetime,
) -> dict[str, Any]:
    return {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "created_at": _utc(created_at).isoformat(),
        "source_snapshot_id": report["data_trust"]["source_snapshot_id"],
        "spec_sha256": report["frozen_specification"]["spec_sha256"],
        "validation_as_of": report["data_trust"]["validation_as_of"],
        "post_freeze_fold_count": fold_count,
        "report_sha256": _report_sha256(report),
        "authority": _authority(),
        "robustness_report": report,
    }


def _state_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, float]]:
    total_bars = sum(int(row["bars"]) for row in rows)
    return {
        str(row["market_state"]): {
            "bars": int(row["bars"]),
            "share": int(row["bars"]) / total_bars if total_bars else 0.0,
            "return_delta": float(row["return_delta"]),
            "return_delta_per_bar": (
                float(row["return_delta"]) / int(row["bars"])
                if int(row["bars"])
                else 0.0
            ),
        }
        for row in rows
    }


def _forward_state_rows(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    totals: dict[str, dict[str, float | int]] = {}
    for fold in report["walk_forward"]["folds"]:
        if fold["lineage"] != "POST_FREEZE_FORWARD":
            continue
        for row in fold.get("market_state_evidence", []):
            state = str(row["market_state"])
            bucket = totals.setdefault(
                state, {"bars": 0, "baseline_return": 0.0, "challenger_return": 0.0}
            )
            bucket["bars"] += int(row["bars"])
            bucket["baseline_return"] += float(row["baseline_return"])
            bucket["challenger_return"] += float(row["challenger_return"])
    return [
        {
            "market_state": state,
            **values,
            "return_delta": float(values["challenger_return"])
            - float(values["baseline_return"]),
        }
        for state, values in sorted(totals.items())
    ]


def _drift(
    baseline: Mapping[str, Any],
    latest: Mapping[str, Any],
    settings: FrozenMonitorSettings,
) -> dict[str, Any]:
    latest_report = latest["robustness_report"]
    post_count = int(latest["post_freeze_fold_count"])
    if post_count == 0:
        return {
            "status": "INSUFFICIENT_FORWARD_EVIDENCE",
            "post_freeze_fold_count": 0,
            "state_mix": [],
            "state_outcomes": [],
            "cost_sensitivity": [],
            "alerts": [],
            "highest_severity": "NONE",
        }

    reference_states = _state_metrics(
        baseline["robustness_report"]["market_state_evidence"]
    )
    forward_rows = _forward_state_rows(latest_report)
    forward_states = _state_metrics(forward_rows)
    state_names = sorted(set(reference_states) | set(forward_states))
    state_mix = []
    state_outcomes = []
    for state in state_names:
        reference = reference_states.get(
            state, {"bars": 0, "share": 0.0, "return_delta_per_bar": 0.0}
        )
        forward = forward_states.get(
            state, {"bars": 0, "share": 0.0, "return_delta_per_bar": 0.0}
        )
        state_mix.append(
            {
                "market_state": state,
                "reference_share": reference["share"],
                "forward_share": forward["share"],
                "share_delta": forward["share"] - reference["share"],
                "forward_bars": forward["bars"],
            }
        )
        state_outcomes.append(
            {
                "market_state": state,
                "reference_return_delta_per_bar": reference["return_delta_per_bar"],
                "forward_return_delta_per_bar": forward["return_delta_per_bar"],
                "deterioration_per_bar": (
                    forward["return_delta_per_bar"]
                    - reference["return_delta_per_bar"]
                ),
                "forward_bars": forward["bars"],
            }
        )

    reference_stress = {
        str(row["id"]): float(row["deltas"]["total_return"])
        for row in baseline["robustness_report"]["stress_matrix"]
    }
    cost_sensitivity = [
        {
            "scenario": str(row["id"]),
            "reference_return_delta": reference_stress[str(row["id"])],
            "current_return_delta": float(row["deltas"]["total_return"]),
            "deterioration": (
                float(row["deltas"]["total_return"])
                - reference_stress[str(row["id"])]
            ),
        }
        for row in latest_report["stress_matrix"]
    ]

    alerts: list[dict[str, Any]] = []
    max_mix = max(state_mix, key=lambda row: abs(row["share_delta"]))
    if abs(max_mix["share_delta"]) >= settings.state_mix_shift_limit:
        alerts.append(
            _alert(
                "STATE_MIX_DRIFT",
                "HIGH",
                f"absolute state-share shift >= {settings.state_mix_shift_limit:.0%}",
                "Forward evidence is concentrated differently from the frozen reference.",
                max_mix,
                "Inspect source continuity and continue the frozen observation; do not retune.",
                "Absolute state-share shift returns below the fixed limit in later complete folds.",
            )
        )
    eligible_outcomes = [row for row in state_outcomes if row["forward_bars"] >= 24]
    worst_outcome = min(
        eligible_outcomes,
        key=lambda row: row["deterioration_per_bar"],
        default=None,
    )
    if (
        worst_outcome is not None
        and worst_outcome["deterioration_per_bar"]
        <= -settings.state_outcome_deterioration_per_bar
    ):
        alerts.append(
            _alert(
                "STATE_OUTCOME_DRIFT",
                "HIGH",
                "per-state return delta deteriorated beyond the frozen limit",
                "A market state is performing materially worse than the frozen reference.",
                worst_outcome,
                "Review the affected state evidence and keep collecting unchanged-policy folds.",
                "The affected state's deterioration returns inside the fixed limit.",
            )
        )
    worst_cost = min(cost_sensitivity, key=lambda row: row["deterioration"])
    if (
        worst_cost["current_return_delta"] < 0
        or worst_cost["deterioration"] <= -settings.cost_return_deterioration_limit
    ):
        alerts.append(
            _alert(
                "COST_SENSITIVITY_DRIFT",
                "CRITICAL" if worst_cost["current_return_delta"] < 0 else "HIGH",
                "stressed return delta is negative or deteriorated beyond the fixed limit",
                "The low-turnover benefit may no longer survive modeled execution costs.",
                worst_cost,
                "Verify fee, slippage and funding inputs; continue frozen observation only.",
                "Every stress scenario is non-negative and inside the fixed deterioration limit.",
            )
        )
    post_folds = [
        row for row in latest_report["walk_forward"]["folds"]
        if row["lineage"] == "POST_FREEZE_FORWARD"
    ]
    latest_fold = post_folds[-1]
    if latest_fold["deltas"]["total_return"] <= -settings.latest_fold_loss_limit:
        alerts.append(
            _alert(
                "LATEST_FOLD_MATERIAL_LOSS",
                "CRITICAL",
                f"latest return delta <= -{settings.latest_fold_loss_limit:.0%}",
                "The latest independent weekly fold is materially adverse.",
                {
                    "test_end_at": latest_fold["test_end_at"],
                    "return_delta": latest_fold["deltas"]["total_return"],
                },
                "Investigate data and risk evidence; do not tune or activate the challenger.",
                "A later governed review resolves the adverse evidence without rewriting it.",
            )
        )
    win_rate = sum(row["deltas"]["total_return"] > 0 for row in post_folds) / len(post_folds)
    if len(post_folds) >= 2 and win_rate < 0.50:
        alerts.append(
            _alert(
                "FORWARD_FOLD_REVERSAL",
                "HIGH",
                "post-freeze win rate < 50% after at least two complete folds",
                "Independent persistence is weaker than the fixed evidence gate requires.",
                {"folds": len(post_folds), "win_rate": win_rate},
                "Continue collecting the frozen strategy and perform human review.",
                "The unchanged-policy post-freeze win rate returns to at least 50%.",
            )
        )
    order = {"NONE": 0, "INFO": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    highest = max((item["severity"] for item in alerts), key=order.get, default="NONE")
    return {
        "status": "ALERT" if highest in {"HIGH", "CRITICAL"} else "STABLE",
        "post_freeze_fold_count": post_count,
        "state_mix": state_mix,
        "state_outcomes": state_outcomes,
        "cost_sensitivity": cost_sensitivity,
        "latest_fold": {
            "test_start_at": latest_fold["test_start_at"],
            "test_end_at": latest_fold["test_end_at"],
            "return_delta": latest_fold["deltas"]["total_return"],
        },
        "post_freeze_win_rate": win_rate,
        "alerts": alerts,
        "highest_severity": highest,
    }


def build_frozen_forward_evidence_view(
    store: MarketStore,
    *,
    snapshot_id: str | None = None,
    settings: FrozenMonitorSettings = FrozenMonitorSettings(),
    observed_at: datetime | None = None,
) -> dict[str, Any]:
    source = _source(store, snapshot_id)
    if isinstance(source, dict):
        return source
    diagnostic, source_id, snapshot = source
    current = _utc(observed_at or datetime.now(timezone.utc))
    frozen_at = _utc(snapshot["as_of"])
    spec = frozen_specification(source_id, frozen_at.isoformat())
    try:
        schedule = _fold_schedule(
            store, snapshot, settings=settings.robustness, observed_at=current
        )
        checkpoints = store.load_frozen_robustness_checkpoints(
            spec_sha256=spec["spec_sha256"]
        )
    except ValueError as exc:
        return _degraded(str(exc), source_id)
    counts = [int(payload["post_freeze_fold_count"]) for _, payload in checkpoints]
    if counts and counts != list(range(counts[-1] + 1)):
        return _degraded("FROZEN_CHECKPOINT_LINEAGE_BROKEN", source_id)
    available = len(schedule["post_freeze_boundaries"])
    latest_count = counts[-1] if counts else -1
    if latest_count > available:
        return _degraded("FROZEN_CHECKPOINT_AHEAD_OF_MARKET_DATA", source_id)
    for _, payload in checkpoints:
        count = int(payload["post_freeze_fold_count"])
        expected = (
            frozen_at
            if count == 0
            else schedule["post_freeze_boundaries"][count - 1]
        )
        if _utc(payload["validation_as_of"]) != expected:
            return _degraded("FROZEN_CHECKPOINT_BOUNDARY_MISMATCH", source_id)
    due = available + 1 if latest_count < 0 else max(0, available - latest_count)
    next_boundary = (
        frozen_at
        if latest_count < 0
        else schedule["post_freeze_boundaries"][latest_count]
        if 0 <= latest_count < available
        else schedule["next_boundary"]
    )
    alerts = []
    if not checkpoints:
        alerts.append(
            _alert(
                "FROZEN_BASELINE_CHECKPOINT_MISSING",
                "HIGH",
                "no immutable fold-zero checkpoint is archived",
                "Drift cannot be measured against a verified frozen reference.",
                {"spec_sha256": spec["spec_sha256"]},
                "Run one explicit PAPER_ONLY evidence WAKE.",
                "Checkpoint zero exists and passes content-hash verification.",
            )
        )
        drift = {
            "status": "BASELINE_REQUIRED",
            "post_freeze_fold_count": 0,
            "state_mix": [],
            "state_outcomes": [],
            "cost_sensitivity": [],
            "alerts": alerts,
            "highest_severity": "HIGH",
        }
        latest_gate = None
    else:
        baseline = checkpoints[0][1]
        latest = checkpoints[-1][1]
        drift = _drift(baseline, latest, settings)
        latest_gate = latest["robustness_report"]["review_gate"]
    checkpoint_rows = [
        {
            "checkpoint_id": checkpoint_id,
            "post_freeze_fold_count": payload["post_freeze_fold_count"],
            "validation_as_of": payload["validation_as_of"],
            "created_at": payload["created_at"],
            "report_sha256": payload["report_sha256"],
            "disposition": payload["robustness_report"]["review_gate"]["disposition"],
            "overfit_level": payload["robustness_report"]["overfit_assessment"]["level"],
        }
        for checkpoint_id, payload in checkpoints
    ]
    disposition = (
        "DRIFT_ALERT"
        if drift["status"] == "ALERT"
        else "EVIDENCE_GATE_RECALCULATED"
        if latest_count >= settings.robustness.min_post_freeze_folds
        else "COLLECTING_FORWARD_EVIDENCE"
        if checkpoints
        else "INITIAL_CHECKPOINT_REQUIRED"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "status": "READY",
        "generated_at": current.isoformat(),
        "data_trust": {
            **diagnostic["data_trust"],
            "current_closed_boundary": schedule["current_boundary"].isoformat(),
            "per_asset_closed_boundary": {
                symbol: boundary.isoformat() if boundary else None
                for symbol, boundary in schedule["per_asset_boundary"].items()
            },
            "checkpoint_hashes_verified": bool(checkpoints),
        },
        "authority": _authority(),
        "frozen_specification": spec,
        "collection": {
            "checkpoint_count": len(checkpoints),
            "latest_archived_post_freeze_fold_count": max(latest_count, 0),
            "available_post_freeze_fold_count": available,
            "minimum_required_post_freeze_folds": settings.robustness.min_post_freeze_folds,
            "new_checkpoint_count_due": due,
            "next_eligible_boundary": next_boundary.isoformat(),
            "next_eligible_after": (next_boundary + schedule["interval"]).isoformat(),
            "checkpoints": checkpoint_rows,
        },
        "drift": drift,
        "latest_robustness_gate": latest_gate,
        "review_gate": {
            "disposition": disposition,
            "latest_mil329_disposition": (
                latest_gate["disposition"] if latest_gate else "UNAVAILABLE"
            ),
            "blocking_reasons": (
                latest_gate["blocking_checks"] if latest_gate else ["BASELINE_REQUIRED"]
            ),
            "requires_human_review": True,
            "parameter_tuning_allowed": False,
            "proposal_creation_allowed": False,
            "challenger_activation_allowed": False,
            "live_execution_allowed": False,
        },
    }


def run_frozen_evidence_cycle(
    store: MarketStore,
    *,
    snapshot_id: str | None = None,
    settings: FrozenMonitorSettings = FrozenMonitorSettings(),
    now: datetime | None = None,
) -> dict[str, Any]:
    current = _utc(now or datetime.now(timezone.utc))
    source = _source(store, snapshot_id)
    if isinstance(source, dict):
        return {"status": "DEGRADED", "archived": [], "view": source}
    _, source_id, snapshot = source
    frozen_at = _utc(snapshot["as_of"])
    spec = frozen_specification(source_id, frozen_at.isoformat())
    try:
        schedule = _fold_schedule(
            store, snapshot, settings=settings.robustness, observed_at=current
        )
        checkpoints = store.load_frozen_robustness_checkpoints(
            spec_sha256=spec["spec_sha256"]
        )
    except ValueError as exc:
        view = _degraded(str(exc), source_id)
        return {"status": "DEGRADED", "archived": [], "view": view}
    latest_count = (
        int(checkpoints[-1][1]["post_freeze_fold_count"]) if checkpoints else -1
    )
    available = len(schedule["post_freeze_boundaries"])
    targets: list[tuple[int, datetime]] = []
    if latest_count < 0:
        targets.append((0, frozen_at))
        latest_count = 0
    targets.extend(
        (count, schedule["post_freeze_boundaries"][count - 1])
        for count in range(latest_count + 1, available + 1)
    )
    targets = targets[: settings.max_new_checkpoints_per_cycle]
    archived = []
    for fold_count, boundary in targets:
        report = build_frozen_challenger_robustness(
            store,
            snapshot_id=source_id,
            settings=settings.robustness,
            observed_at=boundary + schedule["interval"],
        )
        if report["status"] != "READY":
            return {
                "status": "DEGRADED",
                "archived": archived,
                "view": _degraded(
                    f"ROBUSTNESS_{report['data_trust']['reason']}", source_id
                ),
            }
        post = next(
            row for row in report["walk_forward"]["lineage_summary"]
            if row["lineage"] == "POST_FREEZE_FORWARD"
        )
        if int(post["folds"]) != fold_count:
            raise ValueError("frozen checkpoint schedule/report fold mismatch")
        payload = _checkpoint_payload(report, fold_count=fold_count, created_at=current)
        checkpoint_id = store.archive_frozen_robustness_checkpoint(payload)
        archived.append(
            {
                "checkpoint_id": checkpoint_id,
                "post_freeze_fold_count": fold_count,
                "validation_as_of": report["data_trust"]["validation_as_of"],
            }
        )
    view = build_frozen_forward_evidence_view(
        store, snapshot_id=source_id, settings=settings, observed_at=current
    )
    return {
        "schema_version": "mil3.frozen-forward-evidence-cycle.v1",
        "execution_mode": EXECUTION_MODE,
        "status": "ARCHIVED" if archived else "WAITING",
        "evaluated_at": current.isoformat(),
        "archived": archived,
        "authority": _authority(),
        "view": view,
    }


def run_frozen_evidence_scheduler(
    store: MarketStore,
    *,
    interval_seconds: float,
    max_cycles: int | None = None,
    snapshot_id: str | None = None,
    settings: FrozenMonitorSettings = FrozenMonitorSettings(),
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    sleeper: Callable[[float], None] = time.sleep,
    on_cycle: Callable[[dict[str, Any]], None] | None = None,
) -> list[dict[str, Any]]:
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")
    if max_cycles is not None and max_cycles <= 0:
        raise ValueError("max_cycles must be positive when supplied")
    completed = []
    while max_cycles is None or len(completed) < max_cycles:
        summary = run_frozen_evidence_cycle(
            store, snapshot_id=snapshot_id, settings=settings, now=clock()
        )
        completed.append(summary)
        if on_cycle is not None:
            on_cycle(summary)
        if max_cycles is not None and len(completed) >= max_cycles:
            break
        sleeper(interval_seconds)
    return completed
