from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .evidence_export import verify_forward_evidence_bundle


EXECUTION_MODE = "PAPER_ONLY"
VERIFICATION_SCHEMA_VERSION = "mil3.offline-evidence-verification.v1"
RETENTION_SCHEMA_VERSION = "mil3.evidence-retention-receipt.v1"
DEFAULT_RETENTION_DAYS = 365
DEFAULT_MINIMUM_COPIES = 2
_ARCHIVE_PATTERN = re.compile(
    r"^forward-evidence-([0-9a-f]{24})-([0-9a-f]{16})-(\d{8}T\d{6}Z)\.json$"
)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _strict_object(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_evidence_file(path: str | Path) -> tuple[bytes, dict[str, Any]]:
    source = Path(path).expanduser().resolve()
    raw = source.read_bytes()
    payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_object)
    if not isinstance(payload, dict):
        raise ValueError("evidence bundle root must be an object")
    return raw, payload


def build_offline_verification_report(
    path: str | Path,
    *,
    checked_at: datetime | None = None,
) -> dict[str, Any]:
    """Verify one exported bundle without opening or mutating a database."""
    source = Path(path).expanduser().resolve()
    checked = _utc(checked_at or datetime.now(timezone.utc))
    checks: list[dict[str, str]] = []
    raw = b""
    bundle: Mapping[str, Any] = {}
    try:
        raw = source.read_bytes()
        checks.append({"code": "FILE_READ", "status": "PASS"})
    except OSError as exc:
        checks.append({
            "code": "FILE_READ",
            "status": "FAIL",
            "detail": f"{type(exc).__name__}: {exc}",
        })
    try:
        if not raw:
            raise ValueError("evidence file is empty or unreadable")
        bundle = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_strict_object
        )
        if not isinstance(bundle, dict):
            raise ValueError("evidence bundle root must be an object")
        checks.append({"code": "STRICT_JSON", "status": "PASS"})
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        checks.append({
            "code": "STRICT_JSON",
            "status": "FAIL",
            "detail": f"{type(exc).__name__}: {exc}",
        })
    integrity = bool(bundle) and verify_forward_evidence_bundle(bundle)
    checks.append({
        "code": "BUNDLE_INTEGRITY",
        "status": "PASS" if integrity else "FAIL",
    })
    authority = bundle.get("authority", {}) if isinstance(bundle, Mapping) else {}
    authority_locked = bool(
        integrity
        and authority.get("evidence_export_only") is True
        and authority.get("review_action_applies_parameters") is False
        and authority.get("automatic_strategy_change_allowed") is False
        and authority.get("live_execution_allowed") is False
    )
    checks.append({
        "code": "PAPER_AUTHORITY_LOCK",
        "status": "PASS" if authority_locked else "FAIL",
    })
    verified = all(item["status"] == "PASS" for item in checks)
    manifest = bundle.get("manifest", {}) if verified else {}
    return {
        "schema_version": VERIFICATION_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "checked_at": checked.isoformat(),
        "status": "VERIFIED" if verified else "INVALID",
        "source": {
            "path": str(source),
            "size_bytes": len(raw),
            "file_sha256": _sha256_bytes(raw),
        },
        "bundle_identity": {
            "trial_id": bundle.get("trial_id") if verified else None,
            "target_strategy": bundle.get("target_strategy") if verified else None,
            "lifecycle_state": bundle.get("lifecycle_state") if verified else None,
            "combined_sha256": manifest.get("combined_sha256") if verified else None,
            "observation_count": manifest.get("observation_count") if verified else None,
            "review_count": manifest.get("review_count") if verified else None,
        },
        "checks": checks,
        "database_accessed": False,
        "configuration_applied": False,
        "live_execution_allowed": False,
    }


def verification_receipt_hash(report: Mapping[str, Any]) -> str:
    receipt = copy.deepcopy(dict(report))
    receipt.pop("checked_at", None)
    receipt.get("source", {}).pop("path", None)
    canonical = json.dumps(
        receipt, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def write_verification_report(report: Mapping[str, Any], output: str | Path) -> Path:
    path = Path(output).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    return path


def retain_verified_evidence(
    source: str | Path,
    archive_dir: str | Path,
    *,
    retention_days: int = DEFAULT_RETENTION_DAYS,
    minimum_copies: int = DEFAULT_MINIMUM_COPIES,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Copy verified evidence into a scoped archive and prune only known artifacts."""
    if retention_days <= 0 or minimum_copies <= 0:
        raise ValueError("retention_days and minimum_copies must be positive")
    source_path = Path(source).expanduser().resolve()
    archive = Path(archive_dir).expanduser().resolve()
    if source_path == archive or source_path.is_relative_to(archive):
        raise ValueError("source and evidence archive must be separate directories")
    timestamp = _utc(now or datetime.now(timezone.utc))
    verification = build_offline_verification_report(source_path, checked_at=timestamp)
    if verification["status"] != "VERIFIED":
        raise ValueError("evidence retention requires a verified bundle")
    identity = verification["bundle_identity"]
    trial_id = str(identity["trial_id"])
    combined = str(identity["combined_sha256"])
    archive.mkdir(parents=True, exist_ok=True)
    stem = f"forward-evidence-{trial_id}-{combined[:16]}-{timestamp.strftime('%Y%m%dT%H%M%SZ')}"
    destination = archive / f"{stem}.json"
    sidecar = archive / f"{stem}.verification.json"
    temporary = archive / f".{stem}.tmp"
    if destination.exists() or sidecar.exists() or temporary.exists():
        raise FileExistsError(f"evidence backup already exists: {destination}")
    try:
        with source_path.open("rb") as source_handle, temporary.open("xb") as target:
            shutil.copyfileobj(source_handle, target)
            target.flush()
            os.fsync(target.fileno())
        os.link(temporary, destination)
        temporary.unlink()
        retained_verification = build_offline_verification_report(
            destination, checked_at=timestamp
        )
        if (
            retained_verification["status"] != "VERIFIED"
            or retained_verification["source"]["file_sha256"]
            != verification["source"]["file_sha256"]
        ):
            raise ValueError("retained evidence failed copy verification")
        write_verification_report(retained_verification, sidecar)
    except Exception:
        temporary.unlink(missing_ok=True)
        destination.unlink(missing_ok=True)
        sidecar.unlink(missing_ok=True)
        raise

    cutoff = timestamp - timedelta(days=retention_days)
    recognized: dict[str, list[tuple[datetime, Path]]] = {}
    for candidate in archive.glob("forward-evidence-*.json"):
        if candidate.name.endswith(".verification.json"):
            continue
        match = _ARCHIVE_PATTERN.fullmatch(candidate.name)
        if not match:
            continue
        candidate_verification = build_offline_verification_report(
            candidate, checked_at=timestamp
        )
        candidate_identity = candidate_verification["bundle_identity"]
        if (
            candidate_verification["status"] != "VERIFIED"
            or candidate_identity.get("trial_id") != match.group(1)
            or not str(candidate_identity.get("combined_sha256", "")).startswith(
                match.group(2)
            )
        ):
            continue
        artifact_time = datetime.strptime(match.group(3), "%Y%m%dT%H%M%SZ").replace(
            tzinfo=timezone.utc
        )
        recognized.setdefault(match.group(1), []).append((artifact_time, candidate))
    removed: list[str] = []
    for copies in recognized.values():
        ordered = sorted(copies, key=lambda item: (item[0], item[1].name), reverse=True)
        protected = {path for _, path in ordered[:minimum_copies]}
        for artifact_time, candidate in ordered:
            if candidate in protected or artifact_time >= cutoff:
                continue
            candidate.unlink()
            candidate.with_name(
                candidate.name.removesuffix(".json") + ".verification.json"
            ).unlink(missing_ok=True)
            removed.append(candidate.name)

    receipt = {
        "schema_version": RETENTION_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "created_at": timestamp.isoformat(),
        "source_file_sha256": verification["source"]["file_sha256"],
        "trial_id": trial_id,
        "combined_sha256": combined,
        "retained_bundle": destination.name,
        "verification_sidecar": sidecar.name,
        "retention_days": retention_days,
        "minimum_verified_copies": minimum_copies,
        "removed": sorted(removed),
        "scope": "RECOGNIZED_FORWARD_EVIDENCE_ARTIFACTS_ONLY",
        "database_accessed": False,
        "configuration_applied": False,
        "live_execution_allowed": False,
    }
    inventory_name = (
        f"evidence-inventory-{timestamp.strftime('%Y%m%dT%H%M%SZ')}-"
        f"{_sha256_bytes(json.dumps(receipt, sort_keys=True).encode())[:12]}.json"
    )
    write_verification_report(receipt, archive / inventory_name)
    receipt["inventory"] = inventory_name
    return receipt
