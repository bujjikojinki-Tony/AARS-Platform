from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .forward_review import stability_evidence_hash
from .forward_stability import build_forward_stability
from .storage import MarketStore


EXECUTION_MODE = "PAPER_ONLY"
EVIDENCE_SCHEMA_VERSION = "mil3.forward-evidence-bundle.v1"


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _hash(payload: Any) -> str:
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_forward_evidence_bundle(
    store: MarketStore,
    trial_id: str,
    *,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """Package archived and derived evidence without mutating lifecycle state."""
    trial_envelope = store.get_paper_trial_result(trial_id)
    if trial_envelope is None:
        raise ValueError("forward evidence trial is not archived")
    observations = store.load_forward_observations(trial_id, limit=1000000)
    if not observations:
        raise ValueError("forward evidence export requires observation checkpoints")
    stability = build_forward_stability(observations)
    lifecycle = store.get_forward_candidate_lifecycle(trial_id)
    assert lifecycle is not None
    review_payloads = []
    for item in lifecycle["reviews"]:
        payload = store.get_forward_candidate_review(item["review_id"])
        if payload is None:
            raise ValueError("forward evidence review payload is missing")
        review_payloads.append((item["review_id"], payload))

    trial_payload = trial_envelope["trial"]
    authority = {
        "evidence_export_only": True,
        "review_action_applies_parameters": False,
        "automatic_strategy_change_allowed": False,
        "live_execution_allowed": False,
    }
    context = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "trial_id": trial_id,
        "target_strategy": trial_payload["target_strategy"],
        "lifecycle_state": lifecycle["current_state"],
        "authority": authority,
    }
    component_hashes = {
        "context": _hash(context),
        "trial": _hash(trial_payload),
        "observations": {
            observation_id: _hash(payload)
            for observation_id, payload in observations
        },
        "stability": stability_evidence_hash(stability),
        "reviews": {
            review_id: _hash(payload) for review_id, payload in review_payloads
        },
    }
    combined_hash = _hash(component_hashes)
    generated = _utc(generated_at or datetime.now(timezone.utc))
    return {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "generated_at": generated.isoformat(),
        "trial_id": trial_id,
        "target_strategy": trial_payload["target_strategy"],
        "lifecycle_state": lifecycle["current_state"],
        "evidence": {
            "trial": trial_payload,
            "observations": [
                {"observation_id": observation_id, "payload": payload}
                for observation_id, payload in observations
            ],
            "stability": stability,
            "reviews": [
                {"review_id": review_id, "payload": payload}
                for review_id, payload in review_payloads
            ],
        },
        "manifest": {
            "hash_algorithm": "SHA-256",
            "component_sha256": component_hashes,
            "combined_sha256": combined_hash,
            "observation_count": len(observations),
            "review_count": len(review_payloads),
        },
        "authority": authority,
    }


def verify_forward_evidence_bundle(bundle: Mapping[str, Any]) -> bool:
    if bundle.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
        return False
    if bundle.get("execution_mode") != EXECUTION_MODE:
        return False
    authority = bundle.get("authority", {})
    if (
        authority.get("evidence_export_only") is not True
        or authority.get("review_action_applies_parameters") is not False
        or authority.get("automatic_strategy_change_allowed") is not False
        or authority.get("live_execution_allowed") is not False
    ):
        return False
    evidence = bundle.get("evidence", {})
    manifest = bundle.get("manifest", {})
    stability = evidence.get("stability", {})
    try:
        observations = list(evidence.get("observations", []))
        reviews = list(evidence.get("reviews", []))
        trial = evidence.get("trial")
        expected_lifecycle = (
            reviews[-1]["payload"]["resulting_state"] if reviews else "OBSERVING"
        )
        if (
            bundle.get("target_strategy") != trial["target_strategy"]
            or bundle.get("lifecycle_state") != expected_lifecycle
            or stability.get("trial_id") != bundle.get("trial_id")
            or stability.get("target_strategy") != bundle.get("target_strategy")
            or any(
                item["payload"].get("trial_id") != bundle.get("trial_id")
                or item["payload"].get("target_strategy") != bundle.get("target_strategy")
                for item in observations + reviews
            )
        ):
            return False
        context = {
            "schema_version": bundle["schema_version"],
            "execution_mode": bundle["execution_mode"],
            "trial_id": bundle["trial_id"],
            "target_strategy": bundle["target_strategy"],
            "lifecycle_state": bundle["lifecycle_state"],
            "authority": authority,
        }
        expected = {
            "context": _hash(context),
            "trial": _hash(trial),
            "observations": {
                str(item["observation_id"]): _hash(item["payload"])
                for item in observations
            },
            "stability": stability_evidence_hash(stability),
            "reviews": {
                str(item["review_id"]): _hash(item["payload"])
                for item in reviews
            },
        }
    except (KeyError, TypeError, ValueError):
        return False
    return bool(
        manifest.get("component_sha256") == expected
        and manifest.get("combined_sha256") == _hash(expected)
        and manifest.get("observation_count") == len(observations) == len(expected["observations"])
        and manifest.get("review_count") == len(reviews) == len(expected["reviews"])
    )


def write_forward_evidence_bundle(bundle: Mapping[str, Any], output: str | Path) -> Path:
    if not verify_forward_evidence_bundle(bundle):
        raise ValueError("forward evidence bundle failed verification")
    path = Path(output).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(bundle, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    return path
