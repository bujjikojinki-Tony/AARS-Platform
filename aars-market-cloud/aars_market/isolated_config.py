from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping

from .storage import MarketStore


EXECUTION_MODE = "PAPER_ONLY"
CONFIGURATION_SCHEMA_VERSION = "mil3.isolated-paper-configuration.v1"
SANDBOX_EVENT_SCHEMA_VERSION = "mil3.isolated-paper-sandbox-event.v1"


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def canonical_sha256(value: Any) -> str:
    canonical = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_isolated_configuration(
    store: MarketStore,
    trial_id: str,
    *,
    registered_at: datetime | None = None,
) -> dict[str, Any]:
    """Materialize one approved configuration into an inert named registry entry."""
    registered = _utc(registered_at or datetime.now(timezone.utc))
    lifecycle = store.get_isolated_activation_lifecycle(trial_id, now=registered)
    latest = lifecycle.get("latest_event")
    if lifecycle["current_state"] != "APPROVED" or latest is None:
        raise ValueError("configuration registration requires a current isolated approval")
    approval = store.get_isolated_activation_review(latest["review_id"])
    if approval is None:
        raise ValueError("isolated activation approval payload is unavailable")
    authority = approval.get("authority", {})
    if (
        authority.get("isolated_paper_activation_allowed") is not True
        or authority.get("approval_applies_configuration") is not False
        or authority.get("shared_configuration_change_allowed") is not False
        or authority.get("automatic_strategy_change_allowed") is not False
        or authority.get("live_execution_allowed") is not False
    ):
        raise ValueError("isolated activation approval exceeds registry authority")
    configuration = approval["configuration_snapshot"]
    configuration_sha256 = canonical_sha256(configuration)
    identity = {
        "trial_id": trial_id,
        "approval_review_id": latest["review_id"],
        "sandbox_id": approval["sandbox_id"],
        "configuration_sha256": configuration_sha256,
    }
    configuration_id = canonical_sha256(identity)[:24]
    return {
        "schema_version": CONFIGURATION_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "configuration_id": configuration_id,
        "registered_at": registered.isoformat(),
        "trial_id": trial_id,
        "target_strategy": approval["target_strategy"],
        "sandbox_id": approval["sandbox_id"],
        "approval_review_id": latest["review_id"],
        "valid_until": approval["valid_until"],
        "configuration_sha256": configuration_sha256,
        "configuration": configuration,
        "source_evidence": dict(approval["source_evidence"]),
        "authority": {
            "registry_entry_inert": True,
            "atomic_sandbox_activation_allowed": True,
            "shared_configuration_change_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        },
    }


def build_sandbox_event(
    store: MarketStore,
    sandbox_id: str,
    *,
    action: str,
    configuration_id: str | None,
    operator: str,
    note: str,
    event_at: datetime | None = None,
) -> dict[str, Any]:
    """Build an optimistic event; storage revalidates and commits it atomically."""
    normalized_action = action.upper()
    if normalized_action not in {"ACTIVATE", "ROLLBACK"}:
        raise ValueError("unsupported isolated sandbox action")
    normalized_operator = operator.strip()
    normalized_note = note.strip()
    if not normalized_operator or not normalized_note:
        raise ValueError("operator and note are required")
    event_time = _utc(event_at or datetime.now(timezone.utc))
    view = store.resolve_isolated_paper_sandbox(sandbox_id, now=event_time)
    if normalized_action == "ACTIVATE":
        if not configuration_id:
            raise ValueError("activation requires configuration_id")
        next_configuration_id = configuration_id
        rollback_of_event_id = None
    else:
        if configuration_id is not None:
            raise ValueError("rollback target is derived from the latest activation")
        activation = view.get("rollback_candidate")
        if activation is None:
            raise ValueError("sandbox has no unrolled activation")
        next_configuration_id = activation["safe_rollback_configuration_id"]
        rollback_of_event_id = activation["event_id"]
    payload = {
        "schema_version": SANDBOX_EVENT_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "event_at": event_time.isoformat(),
        "action": normalized_action,
        "sandbox_id": sandbox_id,
        "operator": normalized_operator,
        "note": normalized_note,
        "expected_state_version": view["state_version"],
        "previous_event_id": view["latest_event_id"],
        "previous_configuration_id": view["stored_configuration_id"],
        "next_configuration_id": next_configuration_id,
        "rollback_of_event_id": rollback_of_event_id,
        "authority": {
            "isolated_registry_pointer_change_only": True,
            "starts_strategy_process": False,
            "shared_configuration_change_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        },
    }
    payload["event_id"] = canonical_sha256(payload)[:24]
    return payload


def build_fail_safe_invalidation_event(
    view: Mapping[str, Any],
    *,
    event_at: datetime,
) -> dict[str, Any]:
    if view.get("effective_state") not in {
        "EXPIRED_FAIL_SAFE",
        "REVOKED_FAIL_SAFE",
        "APPROVAL_MISMATCH_FAIL_SAFE",
    }:
        raise ValueError("sandbox does not require fail-safe invalidation")
    action = {
        "EXPIRED_FAIL_SAFE": "INVALIDATE_EXPIRED",
        "REVOKED_FAIL_SAFE": "INVALIDATE_REVOKED",
        "APPROVAL_MISMATCH_FAIL_SAFE": "INVALIDATE_APPROVAL_MISMATCH",
    }[str(view["effective_state"])]
    payload = {
        "schema_version": SANDBOX_EVENT_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "event_at": _utc(event_at).isoformat(),
        "action": action,
        "sandbox_id": view["sandbox_id"],
        "operator": "aars-expiry-reconciler",
        "note": view["blocking_reason"],
        "expected_state_version": view["state_version"],
        "previous_event_id": view["latest_event_id"],
        "previous_configuration_id": view["stored_configuration_id"],
        "next_configuration_id": None,
        "rollback_of_event_id": None,
        "authority": {
            "isolated_registry_pointer_change_only": True,
            "starts_strategy_process": False,
            "shared_configuration_change_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        },
    }
    payload["event_id"] = canonical_sha256(payload)[:24]
    return payload
