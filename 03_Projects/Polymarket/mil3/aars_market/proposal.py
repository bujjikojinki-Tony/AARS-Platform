from __future__ import annotations

import math
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Mapping

from .validation import ValidationCandidate


EXECUTION_MODE = "PAPER_ONLY"
PROPOSAL_SCHEMA_VERSION = "mil3.paper-configuration-proposal.v1"
REVIEW_SCHEMA_VERSION = "mil3.paper-proposal-review.v1"
REVIEW_DISPOSITIONS = frozenset(
    {"ACKNOWLEDGED_FOR_PAPER_TRIAL", "DECLINED"}
)

_PARAMETERS = (
    "aars_max_abs_exposure",
    "futures_leverage",
    "grid_spacing_pct",
    "grid_levels",
    "tactical_hedge",
)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _markets(validation: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return list(validation.get("markets", [validation]))


def candidate_from_parameters(
    value: Mapping[str, Any], target: str, *, label: str
) -> dict[str, Any]:
    required = ("target_strategy", *_PARAMETERS)
    missing = [name for name in required if name not in value]
    if missing:
        raise ValueError(f"{label} parameters missing: {', '.join(missing)}")
    if value["target_strategy"] != target:
        raise ValueError(f"{label} target strategy differs from proposal target")
    if not isinstance(value["tactical_hedge"], bool):
        raise ValueError(f"invalid {label} parameters")
    if (
        isinstance(value["grid_levels"], bool)
        or not isinstance(value["grid_levels"], (int, float))
        or not float(value["grid_levels"]).is_integer()
    ):
        raise ValueError(f"invalid {label} parameters")
    try:
        numeric = (
            float(value["aars_max_abs_exposure"]),
            float(value["futures_leverage"]),
            float(value["grid_spacing_pct"]),
        )
        if any(not math.isfinite(item) for item in numeric):
            raise ValueError
        candidate = ValidationCandidate(
            target_strategy=str(value["target_strategy"]),
            aars_max_abs_exposure=numeric[0],
            futures_leverage=numeric[1],
            grid_spacing_pct=numeric[2],
            grid_levels=int(value["grid_levels"]),
            tactical_hedge=bool(value["tactical_hedge"]),
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid {label} parameters") from exc
    if "candidate_id" in value and value["candidate_id"] != candidate.candidate_id:
        raise ValueError(f"{label} candidate id does not match its parameters")
    return candidate.as_dict()


def _selected_candidates(
    snapshot: Mapping[str, Any], target: str
) -> list[tuple[str, dict[str, Any]]]:
    selections: list[tuple[str, dict[str, Any]]] = []
    for market in _markets(snapshot["validation"]):
        folds = market.get("folds", [])
        if not folds:
            continue
        symbol = str(market["market"]["symbol"])
        selections.append(
            (
                symbol,
                candidate_from_parameters(
                    folds[-1]["selected_candidate"], target, label=f"{symbol} selected"
                ),
            )
        )
    return selections


def _default_baseline(target: str) -> dict[str, Any]:
    common = {
        "target_strategy": target,
        "aars_max_abs_exposure": 1.0,
        "futures_leverage": 10.0,
        "grid_spacing_pct": 0.01,
        "grid_levels": 5,
        "tactical_hedge": True,
    }
    if target == "AARS_DYNAMIC":
        common["candidate_id"] = "AARS_DYNAMIC:exposure=1"
    elif target == "SPOT_GRID":
        common["candidate_id"] = "SPOT_GRID:spacing=0.01:levels=5"
    elif target == "FUTURES_LONG_GRID":
        common["candidate_id"] = (
            "FUTURES_LONG_GRID:leverage=10:spacing=0.01:levels=5:hedge=on"
        )
    else:
        raise ValueError(f"unsupported proposal target strategy: {target}")
    return common


def _changes(
    baseline: Mapping[str, Any], proposed: Mapping[str, Any]
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for name in _PARAMETERS:
        before = baseline[name]
        after = proposed[name]
        if before == after:
            continue
        numeric = (
            isinstance(before, (int, float))
            and not isinstance(before, bool)
            and isinstance(after, (int, float))
            and not isinstance(after, bool)
        )
        absolute = float(after) - float(before) if numeric else None
        relative = absolute / abs(float(before)) if numeric and before else None
        result.append(
            {
                "parameter": name,
                "before": before,
                "after": after,
                "absolute_delta": absolute,
                "relative_delta": relative,
            }
        )
    return result


def build_paper_configuration_proposal(
    governance: Mapping[str, Any],
    snapshot_id: str,
    snapshot: Mapping[str, Any],
    *,
    baseline_parameters: Mapping[str, Any] | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """Build an advisory paper proposal from immutable promotion evidence."""
    if governance.get("schema_version") != "mil3.promotion-governance.v1":
        raise ValueError("unsupported promotion governance schema")
    decision = governance.get("decision", {})
    if governance.get("execution_mode") != EXECUTION_MODE:
        raise ValueError("paper proposal requires PAPER_ONLY governance")
    if decision.get("disposition") != "PROMOTION_CANDIDATE":
        raise ValueError("paper proposal requires PROMOTION_CANDIDATE governance")
    if decision.get("automatic_strategy_change_allowed") is not False:
        raise ValueError("governance must lock automatic strategy changes")
    if decision.get("live_execution_allowed") is not False:
        raise ValueError("governance must disallow live execution")
    if snapshot.get("schema_version") != "mil3.shadow-daily.v1":
        raise ValueError("unsupported shadow snapshot schema")
    if snapshot.get("execution_mode") != EXECUTION_MODE:
        raise ValueError("paper proposal requires a PAPER_ONLY snapshot")
    if snapshot.get("review_gate", {}).get("live_execution_allowed") is not False:
        raise ValueError("snapshot must explicitly disallow live execution")
    if not snapshot_id:
        raise ValueError("source snapshot id is required")

    target = str(snapshot["configuration"]["validation_strategy"])
    if governance.get("target_strategy") != target:
        raise ValueError("governance and snapshot target strategies differ")
    selections = _selected_candidates(snapshot, target)
    if not selections:
        raise ValueError("latest snapshot contains no selected candidates")
    counts = Counter(candidate["candidate_id"] for _, candidate in selections)
    selected_id = sorted(counts, key=lambda item: (-counts[item], item))[0]
    proposed = next(
        candidate for _, candidate in selections if candidate["candidate_id"] == selected_id
    )
    baseline = candidate_from_parameters(
        baseline_parameters or _default_baseline(target), target, label="baseline"
    )
    parameter_changes = _changes(baseline, proposed)
    if not parameter_changes:
        raise ValueError("selected candidate does not change the paper baseline")

    generated = _utc(generated_at or datetime.now(timezone.utc))
    observed = governance["observed"]
    rollback = (
        "Stop the separately configured paper trial if drawdown or liquidation-risk "
        "exceeds the MIL-3.14 candidate threshold, a liquidation approximation breach "
        "occurs, or a high-risk warning recurs. This proposal itself changes nothing."
    )
    return {
        "schema_version": PROPOSAL_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "generated_at": generated.isoformat(),
        "target_strategy": target,
        "status": "PENDING_HUMAN_REVIEW",
        "source_evidence": {
            "shadow_snapshot_id": snapshot_id,
            "shadow_as_of": snapshot["as_of"],
            "governance_generated_at": governance["generated_at"],
            "governance_disposition": decision["disposition"],
            "passing_checks": [
                item["id"] for item in governance["checks"] if item["status"] == "PASS"
            ],
        },
        "selection": {
            "policy": "latest-fold cross-asset mode; candidate_id ascending tie-break",
            "selected_candidate_id": selected_id,
            "selection_count": counts[selected_id],
            "asset_count": len(selections),
            "per_asset": [
                {"symbol": symbol, "candidate_id": candidate["candidate_id"]}
                for symbol, candidate in sorted(selections)
            ],
        },
        "baseline_parameters": baseline,
        "proposed_parameters": proposed,
        "parameter_changes": parameter_changes,
        "expected_risk_impact": {
            "assessment": "NOT_FORECAST",
            "statement": (
                "The proposal repeats an observed out-of-sample candidate; it does not "
                "forecast future risk or return. A separate paper trial is required."
            ),
            "observed_mean_excess_return_vs_buy_hold": observed[
                "mean_excess_return_vs_buy_hold"
            ],
            "observed_max_portfolio_drawdown": observed["max_portfolio_drawdown"],
            "observed_max_liquidation_risk": observed["max_liquidation_risk"],
            "observed_liquidation_events": observed["max_liquidation_events"],
        },
        "review_instructions": {
            "rationale": (
                "The candidate passed every MIL-3.14 promotion-governance check and was "
                "the deterministic mode of the latest per-asset fold selections."
            ),
            "rollback_condition": rollback,
            "acknowledgement_meaning": (
                "Acknowledgement permits consideration of a separately configured "
                "PAPER_ONLY trial. It does not apply parameters."
            ),
        },
        "authority": {
            "proposal_application_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        },
        "review_gate": {
            "disposition": "PENDING_HUMAN_REVIEW",
            "live_execution_allowed": False,
        },
    }


def build_paper_proposal_review(
    proposal_id: str,
    proposal: Mapping[str, Any],
    *,
    disposition: str,
    reviewer: str,
    note: str,
    reviewed_at: datetime | None = None,
) -> dict[str, Any]:
    """Create one terminal, immutable human review record without applying a proposal."""
    if proposal.get("schema_version") != PROPOSAL_SCHEMA_VERSION:
        raise ValueError("unsupported paper proposal schema")
    if proposal.get("execution_mode") != EXECUTION_MODE:
        raise ValueError("paper proposal review requires PAPER_ONLY evidence")
    authority = proposal.get("authority", {})
    if authority.get("proposal_application_allowed") is not False:
        raise ValueError("proposal must explicitly disallow application")
    if authority.get("automatic_strategy_change_allowed") is not False:
        raise ValueError("proposal must lock automatic strategy changes")
    if authority.get("live_execution_allowed") is not False:
        raise ValueError("proposal must disallow live execution")
    normalized_disposition = disposition.upper()
    if normalized_disposition not in REVIEW_DISPOSITIONS:
        raise ValueError("unsupported paper proposal review disposition")
    normalized_reviewer = reviewer.strip()
    normalized_note = note.strip()
    if not normalized_reviewer or not normalized_note:
        raise ValueError("reviewer and note are required")
    reviewed = _utc(reviewed_at or datetime.now(timezone.utc))
    return {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "reviewed_at": reviewed.isoformat(),
        "proposal_id": proposal_id,
        "target_strategy": proposal["target_strategy"],
        "disposition": normalized_disposition,
        "reviewer": normalized_reviewer,
        "note": normalized_note,
        "acknowledgement_applies_parameters": False,
        "automatic_strategy_change_allowed": False,
        "live_execution_allowed": False,
    }
