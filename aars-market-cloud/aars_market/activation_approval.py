from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from .evidence_export import verify_forward_evidence_bundle
from .evidence_offline import verification_receipt_hash
from .storage import MarketStore


EXECUTION_MODE = "PAPER_ONLY"
APPROVAL_SCHEMA_VERSION = "mil3.isolated-paper-activation-review.v1"
INITIAL_ACTIONS = frozenset({
    "APPROVE_ISOLATED_PAPER_ACTIVATION",
    "REJECT_ISOLATED_PAPER_ACTIVATION",
})
ALL_ACTIONS = INITIAL_ACTIONS | {"REVOKE_ISOLATED_PAPER_ACTIVATION"}
_SANDBOX_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{2,63}$")


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _hash(value: Any) -> str:
    canonical = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _authority(approved: bool) -> dict[str, bool]:
    return {
        "isolated_paper_activation_allowed": approved,
        "approval_applies_configuration": False,
        "shared_configuration_change_allowed": False,
        "automatic_strategy_change_allowed": False,
        "live_execution_allowed": False,
    }


def build_isolated_activation_review(
    store: MarketStore,
    bundle: Mapping[str, Any],
    verification_report: Mapping[str, Any],
    *,
    action: str,
    reviewer: str,
    note: str,
    sandbox_id: str,
    reviewed_at: datetime | None = None,
    validity_hours: int = 24,
) -> dict[str, Any]:
    """Build a terminal decision that authorizes only a future isolated sandbox step."""
    normalized_action = action.upper()
    if normalized_action not in INITIAL_ACTIONS:
        raise ValueError("unsupported isolated activation review action")
    if not verify_forward_evidence_bundle(bundle):
        raise ValueError("isolated activation review requires a valid evidence bundle")
    if verification_report.get("status") != "VERIFIED":
        raise ValueError("isolated activation review requires offline verification")
    identity = verification_report.get("bundle_identity", {})
    manifest = bundle["manifest"]
    if (
        identity.get("trial_id") != bundle.get("trial_id")
        or identity.get("combined_sha256") != manifest.get("combined_sha256")
        or verification_report.get("database_accessed") is not False
        or verification_report.get("configuration_applied") is not False
        or verification_report.get("live_execution_allowed") is not False
    ):
        raise ValueError("offline verification receipt differs from evidence bundle")
    normalized_reviewer = reviewer.strip()
    normalized_note = note.strip()
    normalized_sandbox = sandbox_id.strip().lower()
    if not normalized_reviewer or not normalized_note:
        raise ValueError("reviewer and note are required")
    if not _SANDBOX_ID.fullmatch(normalized_sandbox):
        raise ValueError("sandbox_id must be 3-64 lowercase safe characters")
    if not 1 <= validity_hours <= 168:
        raise ValueError("validity_hours must be between 1 and 168")
    if store.get_isolated_activation_lifecycle(str(bundle["trial_id"]))["events"]:
        raise ValueError("isolated activation trial already has a terminal decision")

    approved = normalized_action == "APPROVE_ISOLATED_PAPER_ACTIVATION"
    stability = bundle["evidence"]["stability"]
    reviews = bundle["evidence"]["reviews"]
    warning_codes = list(stability["summary"]["warning_codes"])
    if approved and (
        bundle.get("lifecycle_state") != "OBSERVING_ACKNOWLEDGED"
        or stability.get("review_gate", {}).get("disposition")
        != "EXTENDED_OBSERVATION_CONFIRMED"
        or warning_codes
        or not reviews
        or reviews[-1]["payload"].get("action")
        != "ACKNOWLEDGE_FOR_PAPER_CONTINUATION"
    ):
        raise ValueError("isolated activation approval prerequisites are not satisfied")
    reviewed = _utc(reviewed_at or datetime.now(timezone.utc))
    valid_until = reviewed + timedelta(hours=validity_hours) if approved else None
    trial_configuration = bundle["evidence"]["trial"]["configuration"]
    observations = bundle["evidence"]["observations"]
    return {
        "schema_version": APPROVAL_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "reviewed_at": reviewed.isoformat(),
        "trial_id": bundle["trial_id"],
        "target_strategy": bundle["target_strategy"],
        "action": normalized_action,
        "previous_state": "PENDING_HUMAN_APPROVAL",
        "resulting_state": "APPROVED" if approved else "REJECTED",
        "previous_review_id": None,
        "reviewer": normalized_reviewer,
        "note": normalized_note,
        "sandbox_id": normalized_sandbox,
        "valid_until": valid_until.isoformat() if valid_until else None,
        "source_evidence": {
            "bundle_combined_sha256": manifest["combined_sha256"],
            "bundle_file_sha256": verification_report["source"]["file_sha256"],
            "verification_receipt_sha256": verification_receipt_hash(
                verification_report
            ),
            "latest_observation_id": observations[-1]["observation_id"],
            "stability_sha256": manifest["component_sha256"]["stability"],
            "stability_disposition": stability["review_gate"]["disposition"],
            "warning_codes": warning_codes,
            "configuration_sha256": _hash(trial_configuration),
        },
        "configuration_snapshot": trial_configuration,
        "authority": _authority(approved),
    }


def build_isolated_activation_revocation(
    store: MarketStore,
    trial_id: str,
    *,
    reviewer: str,
    note: str,
    reviewed_at: datetime | None = None,
) -> dict[str, Any]:
    lifecycle = store.get_isolated_activation_lifecycle(trial_id, now=reviewed_at)
    latest = lifecycle.get("latest_event")
    if lifecycle["current_state"] != "APPROVED" or latest is None:
        raise ValueError("only a current isolated approval can be revoked")
    original = store.get_isolated_activation_review(latest["review_id"])
    assert original is not None
    normalized_reviewer = reviewer.strip()
    normalized_note = note.strip()
    if not normalized_reviewer or not normalized_note:
        raise ValueError("reviewer and note are required")
    reviewed = _utc(reviewed_at or datetime.now(timezone.utc))
    return {
        "schema_version": APPROVAL_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "reviewed_at": reviewed.isoformat(),
        "trial_id": trial_id,
        "target_strategy": original["target_strategy"],
        "action": "REVOKE_ISOLATED_PAPER_ACTIVATION",
        "previous_state": "APPROVED",
        "resulting_state": "REVOKED",
        "previous_review_id": latest["review_id"],
        "reviewer": normalized_reviewer,
        "note": normalized_note,
        "sandbox_id": original["sandbox_id"],
        "valid_until": original["valid_until"],
        "source_evidence": dict(original["source_evidence"]),
        "configuration_snapshot": dict(original["configuration_snapshot"]),
        "authority": _authority(False),
    }
