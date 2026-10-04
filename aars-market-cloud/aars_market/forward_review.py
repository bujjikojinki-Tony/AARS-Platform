from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping

from .storage import MarketStore


EXECUTION_MODE = "PAPER_ONLY"
REVIEW_SCHEMA_VERSION = "mil3.forward-candidate-review.v1"
REVIEW_ACTIONS = frozenset({
    "ACKNOWLEDGE_FOR_PAPER_CONTINUATION",
    "PAUSE_PAPER_OBSERVATION",
    "TERMINATE_PAPER_OBSERVATION",
    "RESTART_PAPER_OBSERVATION",
})


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def stability_evidence_hash(stability: Mapping[str, Any]) -> str:
    evidence = dict(stability)
    evidence.pop("generated_at", None)
    canonical = json.dumps(
        evidence, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def transition_state(current_state: str, action: str, stability_disposition: str) -> str:
    if action not in REVIEW_ACTIONS:
        raise ValueError("unsupported forward candidate review action")
    if current_state == "TERMINATED":
        raise ValueError("terminated forward candidate cannot transition")
    if action == "ACKNOWLEDGE_FOR_PAPER_CONTINUATION":
        if current_state != "OBSERVING":
            raise ValueError("acknowledgement requires observing state")
        if stability_disposition != "EXTENDED_OBSERVATION_CONFIRMED":
            raise ValueError("acknowledgement requires confirmed extended observation")
        return "OBSERVING_ACKNOWLEDGED"
    if action == "PAUSE_PAPER_OBSERVATION":
        if current_state not in {"OBSERVING", "OBSERVING_ACKNOWLEDGED"}:
            raise ValueError("pause requires an active observation state")
        if stability_disposition == "STOP_EXTENDED_OBSERVATION":
            raise ValueError("stopped observation requires termination")
        return "PAUSED"
    if action == "TERMINATE_PAPER_OBSERVATION":
        return "TERMINATED"
    if current_state != "PAUSED":
        raise ValueError("restart requires paused state")
    if stability_disposition not in {
        "CONTINUE_EXTENDED_OBSERVATION",
        "EXTENDED_OBSERVATION_CONFIRMED",
    }:
        raise ValueError("restart requires non-stopped, non-deferred evidence")
    return "OBSERVING"


def build_forward_candidate_review(
    store: MarketStore,
    trial_id: str,
    stability: Mapping[str, Any],
    *,
    action: str,
    reviewer: str,
    note: str,
    reviewed_at: datetime | None = None,
) -> dict[str, Any]:
    """Create one immutable human lifecycle event without applying parameters."""
    if stability.get("schema_version") != "mil3.forward-stability.v1":
        raise ValueError("unsupported forward stability schema")
    if stability.get("execution_mode") != EXECUTION_MODE:
        raise ValueError("forward review requires PAPER_ONLY stability evidence")
    if stability.get("trial_id") != trial_id:
        raise ValueError("forward review trial differs from stability evidence")
    for authority in (stability.get("authority", {}), stability.get("review_gate", {})):
        if any(authority.get(key) is not False for key in (
            "observation_application_allowed",
            "automatic_strategy_change_allowed",
            "live_execution_allowed",
        )):
            raise ValueError("forward stability exceeds review authority")
    normalized_reviewer = reviewer.strip()
    normalized_note = note.strip()
    if not normalized_reviewer or not normalized_note:
        raise ValueError("reviewer and note are required")
    normalized_action = action.upper()
    lifecycle = store.get_forward_candidate_lifecycle(trial_id)
    if lifecycle is None:
        raise ValueError("forward review trial is not archived")
    current_state = str(lifecycle["current_state"])
    stability_disposition = str(stability.get("review_gate", {}).get("disposition", ""))
    resulting_state = transition_state(
        current_state, normalized_action, stability_disposition
    )
    latest = store.latest_forward_observation_for_trial(trial_id)
    if latest is None:
        raise ValueError("forward review requires an archived observation checkpoint")
    previous = lifecycle.get("latest_review")
    reviewed = _utc(reviewed_at or datetime.now(timezone.utc))
    if previous and reviewed <= _utc(datetime.fromisoformat(previous["reviewed_at"])):
        raise ValueError("review time must be later than the previous review")
    return {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "reviewed_at": reviewed.isoformat(),
        "trial_id": trial_id,
        "target_strategy": stability["target_strategy"],
        "action": normalized_action,
        "previous_state": current_state,
        "resulting_state": resulting_state,
        "reviewer": normalized_reviewer,
        "note": normalized_note,
        "previous_review_id": previous["review_id"] if previous else None,
        "source_evidence": {
            "observation_id": latest["observation_id"],
            "observation_input_sha256": latest["input_sha256"],
            "observed_through": latest["observed_through"],
            "stability_disposition": stability_disposition,
            "stability_sha256": stability_evidence_hash(stability),
            "available_checkpoints": stability["summary"]["available_checkpoints"],
            "warning_codes": list(stability["summary"]["warning_codes"]),
        },
        "review_action_applies_parameters": False,
        "automatic_strategy_change_allowed": False,
        "live_execution_allowed": False,
    }
