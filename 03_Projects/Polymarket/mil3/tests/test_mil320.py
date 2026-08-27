from __future__ import annotations

import copy
import json
import subprocess
import sys
from datetime import timedelta
from http import HTTPStatus
from pathlib import Path

import pytest

from aars_market.activation_approval import (
    build_isolated_activation_review,
    build_isolated_activation_revocation,
)
from aars_market.api import make_handler
from aars_market.evidence_export import (
    _hash,
    build_forward_evidence_bundle,
    verify_forward_evidence_bundle,
    write_forward_evidence_bundle,
)
from aars_market.evidence_offline import (
    build_offline_verification_report,
    retain_verified_evidence,
    verification_receipt_hash,
    write_verification_report,
)
from aars_market.forward_review import stability_evidence_hash
from aars_market.service import DashboardService
from tests.test_mil316 import START
from tests.test_mil319 import _observing_store


def _exported_bundle(tmp_path: Path):
    store, trial_id = _observing_store(tmp_path / "market.sqlite")
    bundle = build_forward_evidence_bundle(store, trial_id, generated_at=START)
    path = write_forward_evidence_bundle(bundle, tmp_path / "evidence.json")
    report = build_offline_verification_report(path, checked_at=START)
    return store, trial_id, bundle, path, report


def _confirmed_bundle(bundle: dict) -> dict:
    result = copy.deepcopy(bundle)
    stability = result["evidence"]["stability"]
    stability["review_gate"]["disposition"] = "EXTENDED_OBSERVATION_CONFIRMED"
    stability["summary"]["warning_codes"] = []
    acknowledgement = {
        "schema_version": "mil3.forward-candidate-review.v1",
        "execution_mode": "PAPER_ONLY",
        "reviewed_at": (START + timedelta(hours=1)).isoformat(),
        "trial_id": result["trial_id"],
        "target_strategy": result["target_strategy"],
        "action": "ACKNOWLEDGE_FOR_PAPER_CONTINUATION",
        "previous_state": "OBSERVING",
        "resulting_state": "OBSERVING_ACKNOWLEDGED",
        "reviewer": "local-owner",
        "note": "Confirmed evidence acknowledged for isolated paper review.",
        "review_action_applies_parameters": False,
        "automatic_strategy_change_allowed": False,
        "live_execution_allowed": False,
    }
    result["evidence"]["reviews"] = [
        {"review_id": "acknowledgement-review", "payload": acknowledgement}
    ]
    result["lifecycle_state"] = "OBSERVING_ACKNOWLEDGED"
    components = result["manifest"]["component_sha256"]
    components["stability"] = stability_evidence_hash(stability)
    components["reviews"] = {"acknowledgement-review": _hash(acknowledgement)}
    components["context"] = _hash({
        "schema_version": result["schema_version"],
        "execution_mode": result["execution_mode"],
        "trial_id": result["trial_id"],
        "target_strategy": result["target_strategy"],
        "lifecycle_state": result["lifecycle_state"],
        "authority": result["authority"],
    })
    result["manifest"]["review_count"] = 1
    result["manifest"]["combined_sha256"] = _hash(components)
    assert verify_forward_evidence_bundle(result)
    return result


def test_offline_verification_is_database_independent_strict_and_non_overwriting(tmp_path: Path):
    _, trial_id, _, path, report = _exported_bundle(tmp_path)
    assert report["status"] == "VERIFIED"
    assert report["bundle_identity"]["trial_id"] == trial_id
    assert report["database_accessed"] is False
    receipt = verification_receipt_hash(report)
    assert len(receipt) == 64
    assert report["source"]["path"] == str(path.resolve())
    output = write_verification_report(report, tmp_path / "verification.json")
    with pytest.raises(FileExistsError):
        write_verification_report(report, output)

    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"schema_version":"x","schema_version":"y"}', encoding="utf-8")
    invalid = build_offline_verification_report(duplicate, checked_at=START)
    assert invalid["status"] == "INVALID"
    assert invalid["checks"][1]["code"] == "STRICT_JSON"
    assert invalid["checks"][1]["status"] == "FAIL"
    assert len(invalid["source"]["file_sha256"]) == 64


def test_scoped_retention_verifies_copy_preserves_floor_and_unknown_files(tmp_path: Path):
    _, trial_id, _, path, _ = _exported_bundle(tmp_path)
    archive = tmp_path / "archive"
    unknown = archive / "operator-note.txt"
    archive.mkdir()
    unknown.write_text("keep", encoding="utf-8")
    lookalike = archive / (
        f"forward-evidence-{trial_id}-{'0' * 16}-20200101T000000Z.json"
    )
    lookalike.write_text("operator-owned lookalike", encoding="utf-8")
    first = retain_verified_evidence(
        path, archive, retention_days=30, minimum_copies=2, now=START
    )
    second = retain_verified_evidence(
        path, archive, retention_days=30, minimum_copies=2,
        now=START + timedelta(days=1),
    )
    third = retain_verified_evidence(
        path, archive, retention_days=30, minimum_copies=2,
        now=START + timedelta(days=40),
    )
    assert first["trial_id"] == trial_id
    assert second["removed"] == []
    assert len(third["removed"]) == 1
    assert unknown.read_text(encoding="utf-8") == "keep"
    assert lookalike.read_text(encoding="utf-8") == "operator-owned lookalike"
    retained = list(archive.glob("forward-evidence-*.json"))
    bundles = [
        item for item in retained
        if not item.name.endswith(".verification.json")
        and build_offline_verification_report(item)["status"] == "VERIFIED"
    ]
    assert len(bundles) == 2
    assert all(build_offline_verification_report(item)["status"] == "VERIFIED" for item in bundles)


def test_retention_rejects_invalid_or_in_archive_source(tmp_path: Path):
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="requires a verified bundle"):
        retain_verified_evidence(invalid, tmp_path / "archive", now=START)
    archive = tmp_path / "same"
    archive.mkdir()
    nested = archive / "bundle.json"
    nested.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="separate directories"):
        retain_verified_evidence(nested, archive, now=START)


def test_isolated_review_rejects_unconfirmed_approval_but_allows_terminal_rejection(tmp_path: Path):
    store, trial_id, bundle, _, report = _exported_bundle(tmp_path)
    with pytest.raises(ValueError, match="prerequisites"):
        build_isolated_activation_review(
            store, bundle, report,
            action="APPROVE_ISOLATED_PAPER_ACTIVATION",
            reviewer="owner", note="Too early.", sandbox_id="paper-sandbox",
            reviewed_at=START,
        )
    rejected = build_isolated_activation_review(
        store, bundle, report,
        action="REJECT_ISOLATED_PAPER_ACTIVATION",
        reviewer="owner", note="Evidence is not ready.", sandbox_id="paper-sandbox",
        reviewed_at=START,
    )
    review_id = store.archive_isolated_activation_review(rejected)
    lifecycle = store.get_isolated_activation_lifecycle(trial_id, now=START)
    assert lifecycle["current_state"] == "REJECTED"
    assert lifecycle["latest_event"]["review_id"] == review_id
    assert rejected["authority"]["isolated_paper_activation_allowed"] is False
    with pytest.raises(ValueError, match="terminal decision"):
        build_isolated_activation_review(
            store, bundle, report,
            action="REJECT_ISOLATED_PAPER_ACTIVATION",
            reviewer="owner", note="Second decision.", sandbox_id="paper-sandbox",
        )


def test_confirmed_isolated_approval_expires_and_can_be_revoked(tmp_path: Path, monkeypatch):
    store, trial_id, base, path, _ = _exported_bundle(tmp_path)
    confirmed = _confirmed_bundle(base)
    path.unlink()
    write_forward_evidence_bundle(confirmed, path)
    report = build_offline_verification_report(path, checked_at=START)
    monkeypatch.setattr(
        "aars_market.evidence_export.build_forward_evidence_bundle",
        lambda selected_store, selected_trial_id: confirmed,
    )
    approved = build_isolated_activation_review(
        store, confirmed, report,
        action="APPROVE_ISOLATED_PAPER_ACTIVATION",
        reviewer="owner", note="Approve isolated paper sandbox only.",
        sandbox_id="paper-sandbox", reviewed_at=START, validity_hours=48,
    )
    approval_id = store.archive_isolated_activation_review(approved)
    current = store.get_isolated_activation_lifecycle(
        trial_id, now=START + timedelta(hours=24)
    )
    assert current["current_state"] == "APPROVED"
    assert current["isolated_paper_activation_allowed"] is True
    assert approved["authority"]["isolated_paper_activation_allowed"] is True
    assert approved["authority"]["approval_applies_configuration"] is False
    expired = store.get_isolated_activation_lifecycle(
        trial_id, now=START + timedelta(hours=49)
    )
    assert expired["current_state"] == "EXPIRED"
    assert expired["isolated_paper_activation_allowed"] is False

    revoked = build_isolated_activation_revocation(
        store, trial_id, reviewer="owner", note="Withdraw sandbox authority.",
        reviewed_at=START + timedelta(hours=24),
    )
    assert revoked["previous_review_id"] == approval_id
    store.archive_isolated_activation_review(revoked)
    assert store.get_isolated_activation_lifecycle(
        trial_id, now=START + timedelta(hours=25)
    )["current_state"] == "REVOKED"


def test_storage_revalidates_bundle_configuration_and_authority(tmp_path: Path):
    store, _, bundle, _, report = _exported_bundle(tmp_path)
    rejected = build_isolated_activation_review(
        store, bundle, report,
        action="REJECT_ISOLATED_PAPER_ACTIVATION",
        reviewer="owner", note="Reject.", sandbox_id="paper-sandbox",
        reviewed_at=START,
    )
    tampered = copy.deepcopy(rejected)
    tampered["configuration_snapshot"]["settings"]["fee_rate"] = 0.99
    with pytest.raises(ValueError, match="source evidence changed"):
        store.archive_isolated_activation_review(tampered)
    excessive = copy.deepcopy(rejected)
    excessive["authority"]["live_execution_allowed"] = True
    with pytest.raises(ValueError, match="exceeds sandbox authority"):
        store.archive_isolated_activation_review(excessive)


def test_policy_activation_and_review_apis_are_read_only(tmp_path: Path):
    store, trial_id, bundle, _, report = _exported_bundle(tmp_path)
    rejected = build_isolated_activation_review(
        store, bundle, report,
        action="REJECT_ISOLATED_PAPER_ACTIVATION",
        reviewer="owner", note="Reject for API.", sandbox_id="paper-sandbox",
        reviewed_at=START,
    )
    review_id = store.archive_isolated_activation_review(rejected)
    handler_type = make_handler(DashboardService(store), tmp_path)
    handler = object.__new__(handler_type)
    handler.path = "/api/v1/evidence-governance-policy"
    status, policy = handler._api_payload()
    assert status == HTTPStatus.OK
    assert policy["minimum_verified_copies"] == 2
    assert policy["live_execution_allowed"] is False
    handler.path = f"/api/v1/isolated-activation?trial_id={trial_id}"
    status, lifecycle = handler._api_payload()
    assert status == HTTPStatus.OK
    assert lifecycle["current_state"] == "REJECTED"
    assert lifecycle["isolated_paper_activation_allowed"] is False
    assert lifecycle["approval_applies_configuration"] is False
    handler.path = f"/api/v1/isolated-activation-reviews/{review_id}"
    status, envelope = handler._api_payload()
    assert status == HTTPStatus.OK
    assert envelope["review"]["sandbox_id"] == "paper-sandbox"
    assert envelope["live_execution_allowed"] is False


def test_offline_and_rejection_clis_are_explicit_local_paths(tmp_path: Path):
    store, trial_id, _, path, _ = _exported_bundle(tmp_path)
    root = Path(__file__).parents[1]
    report_path = tmp_path / "report.json"
    verified = subprocess.run(
        [sys.executable, str(root / "run_forward_evidence_verify.py"),
         "--bundle", str(path), "--report", str(report_path)],
        check=True, capture_output=True, text=True,
    )
    assert "database_accessed=false" in verified.stdout
    assert "status=VERIFIED" in verified.stdout
    retained = subprocess.run(
        [sys.executable, str(root / "run_forward_evidence_retain.py"),
         "--bundle", str(path), "--archive-dir", str(tmp_path / "archive")],
        check=True, capture_output=True, text=True,
    )
    assert '"scope": "RECOGNIZED_FORWARD_EVIDENCE_ARTIFACTS_ONLY"' in retained.stdout
    reviewed = subprocess.run(
        [sys.executable, str(root / "run_isolated_activation_review.py"),
         "--db", store.path, "--trial-id", trial_id,
         "--action", "REJECT_ISOLATED_PAPER_ACTIVATION", "--bundle", str(path),
         "--reviewer", "owner", "--note", "Not ready."],
        check=True, capture_output=True, text=True,
    )
    assert "resulting_state=REJECTED" in reviewed.stdout
    assert "approval_applies_configuration=false" in reviewed.stdout
    assert "live_execution_allowed=false" in reviewed.stdout


def test_mil320_ui_exposes_prerequisites_retention_and_no_web_activation():
    ui_root = Path(__file__).parents[1] / "ui"
    html = (ui_root / "index.html").read_text(encoding="utf-8")
    javascript = (ui_root / "app.js").read_text(encoding="utf-8")
    css = (ui_root / "styles.css").read_text(encoding="utf-8")
    assert "AARS // 03.23" in html
    assert 'id="activation-approval-status"' in html
    assert 'id="activation-prerequisites"' in html
    assert 'id="evidence-retention-policy"' in html
    assert 'id="activation-review-history"' in html
    assert "APPROVAL DOES NOT APPLY CONFIGURATION" in html
    assert "/api/v1/evidence-governance-policy" in javascript
    assert "/api/v1/isolated-activation?trial_id=${encodeURIComponent(latest.trial_id)}" in javascript
    assert "/api/v1/isolated-activation-reviews/${encodeURIComponent(activation.latest_event.review_id)}" in javascript
    assert "isolated activation human review exceeded sandbox authority" in javascript
    assert "THIS SCREEN HAS NO APPROVE OR ACTIVATE BUTTON" in javascript
    assert "run_forward_evidence_verify.py" in javascript
    assert '.activation-prerequisites article[data-status="PASS"]' in css
    assert '.forward-lifecycle-heading > strong[data-status="EXPIRED"]' in css
