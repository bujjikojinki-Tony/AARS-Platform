from __future__ import annotations

import copy
import json
import subprocess
import sys
from datetime import timedelta
from http import HTTPStatus
from pathlib import Path

import pytest

from aars_market.api import make_handler
from aars_market.evidence_export import (
    build_forward_evidence_bundle,
    verify_forward_evidence_bundle,
    write_forward_evidence_bundle,
)
from aars_market.forward_monitor import run_forward_monitor_cycle
from aars_market.forward_review import (
    build_forward_candidate_review,
    transition_state,
)
from aars_market.service import DashboardService
from tests.test_mil316 import START
from tests.test_mil317 import _eligible_trial


def _observing_store(path: Path):
    store, trial_id, _ = _eligible_trial(path)
    first = run_forward_monitor_cycle(store, now=START)
    assert first["records"][0]["status"] == "ARCHIVED"
    return store, trial_id


def _review(store, trial_id: str, action: str, day: int, note: str):
    stability = DashboardService(store).forward_stability(trial_id)
    payload = build_forward_candidate_review(
        store,
        trial_id,
        stability,
        action=action,
        reviewer="local-owner",
        note=note,
        reviewed_at=START + timedelta(days=day),
    )
    review_id = store.archive_forward_candidate_review(payload)
    return review_id, payload


def test_human_review_lifecycle_pause_restart_and_irreversible_termination(tmp_path: Path):
    store, trial_id = _observing_store(tmp_path / "market.sqlite")
    pause_id, pause = _review(
        store, trial_id, "PAUSE_PAPER_OBSERVATION", 1, "Pause for manual risk review."
    )
    assert pause["previous_state"] == "OBSERVING"
    assert pause["resulting_state"] == "PAUSED"
    assert store.get_forward_candidate_lifecycle(trial_id)["current_state"] == "PAUSED"

    restart_id, restart = _review(
        store, trial_id, "RESTART_PAPER_OBSERVATION", 2,
        "Resume the same paper-only candidate after review.",
    )
    assert restart["previous_review_id"] == pause_id
    assert restart["resulting_state"] == "OBSERVING"

    terminate_id, terminate = _review(
        store, trial_id, "TERMINATE_PAPER_OBSERVATION", 3,
        "Retire this candidate and retain its evidence.",
    )
    assert terminate["previous_review_id"] == restart_id
    assert terminate["resulting_state"] == "TERMINATED"
    lifecycle = store.get_forward_candidate_lifecycle(trial_id)
    assert lifecycle["current_state"] == "TERMINATED"
    assert [item["review_id"] for item in lifecycle["reviews"]] == [
        pause_id, restart_id, terminate_id
    ]

    stability = DashboardService(store).forward_stability(trial_id)
    with pytest.raises(ValueError, match="cannot transition"):
        build_forward_candidate_review(
            store, trial_id, stability,
            action="RESTART_PAPER_OBSERVATION", reviewer="owner", note="invalid",
        )


def test_acknowledgement_requires_confirmation_and_actions_never_apply_parameters(tmp_path: Path):
    store, trial_id = _observing_store(tmp_path / "market.sqlite")
    stability = DashboardService(store).forward_stability(trial_id)
    with pytest.raises(ValueError, match="requires confirmed"):
        build_forward_candidate_review(
            store, trial_id, stability,
            action="ACKNOWLEDGE_FOR_PAPER_CONTINUATION",
            reviewer="local-owner", note="Too early.",
        )
    assert transition_state(
        "OBSERVING", "ACKNOWLEDGE_FOR_PAPER_CONTINUATION",
        "EXTENDED_OBSERVATION_CONFIRMED",
    ) == "OBSERVING_ACKNOWLEDGED"
    _, pause = _review(
        store, trial_id, "PAUSE_PAPER_OBSERVATION", 1, "Pause safely."
    )
    assert pause["review_action_applies_parameters"] is False
    assert pause["automatic_strategy_change_allowed"] is False
    assert pause["live_execution_allowed"] is False


def test_review_archive_rejects_stale_source_tamper_and_nonmonotonic_time(tmp_path: Path):
    store, trial_id = _observing_store(tmp_path / "market.sqlite")
    stability = DashboardService(store).forward_stability(trial_id)
    pause = build_forward_candidate_review(
        store, trial_id, stability,
        action="PAUSE_PAPER_OBSERVATION", reviewer="owner", note="Pause.",
        reviewed_at=START + timedelta(days=2),
    )
    stale = copy.deepcopy(pause)
    stale["source_evidence"]["observation_input_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="not latest evidence"):
        store.archive_forward_candidate_review(stale)
    tampered = copy.deepcopy(pause)
    tampered["source_evidence"]["warning_codes"] = ["HIDDEN_WARNING"]
    with pytest.raises(ValueError, match="warning evidence is stale"):
        store.archive_forward_candidate_review(tampered)

    store.archive_forward_candidate_review(pause)
    current = DashboardService(store).forward_stability(trial_id)
    with pytest.raises(ValueError, match="later than"):
        build_forward_candidate_review(
            store, trial_id, current,
            action="RESTART_PAPER_OBSERVATION", reviewer="owner", note="Old time.",
            reviewed_at=START + timedelta(days=1),
        )


def test_monitor_respects_pause_restart_and_termination(tmp_path: Path):
    store, trial_id = _observing_store(tmp_path / "market.sqlite")
    _review(store, trial_id, "PAUSE_PAPER_OBSERVATION", 1, "Pause monitor.")
    paused = run_forward_monitor_cycle(store, now=START + timedelta(days=2))
    assert paused["records"][0]["status"] == "PAUSED"
    _review(store, trial_id, "RESTART_PAPER_OBSERVATION", 2, "Restart monitor.")
    restarted = run_forward_monitor_cycle(store, now=START + timedelta(days=3))
    assert restarted["records"][0]["status"] == "REUSED"
    _review(store, trial_id, "TERMINATE_PAPER_OBSERVATION", 3, "Terminate candidate.")
    terminated = run_forward_monitor_cycle(store, now=START + timedelta(days=4))
    assert terminated["records"][0]["status"] == "TERMINATED"


def test_evidence_bundle_is_deterministic_self_verifying_and_non_overwriting(tmp_path: Path):
    store, trial_id = _observing_store(tmp_path / "market.sqlite")
    _review(store, trial_id, "PAUSE_PAPER_OBSERVATION", 1, "Pause for bundle.")
    first = build_forward_evidence_bundle(store, trial_id, generated_at=START)
    second = build_forward_evidence_bundle(
        store, trial_id, generated_at=START + timedelta(days=1)
    )
    assert first["manifest"]["combined_sha256"] == second["manifest"]["combined_sha256"]
    assert first["manifest"]["observation_count"] == 1
    assert first["manifest"]["review_count"] == 1
    assert verify_forward_evidence_bundle(first) is True
    output = write_forward_evidence_bundle(first, tmp_path / "bundle.json")
    assert json.loads(output.read_text(encoding="utf-8"))["trial_id"] == trial_id
    with pytest.raises(FileExistsError):
        write_forward_evidence_bundle(first, output)
    corrupted = copy.deepcopy(first)
    corrupted["evidence"]["reviews"][0]["payload"]["note"] = "changed"
    assert verify_forward_evidence_bundle(corrupted) is False
    authority_tampered = copy.deepcopy(first)
    authority_tampered["authority"]["live_execution_allowed"] = True
    assert verify_forward_evidence_bundle(authority_tampered) is False
    lifecycle_tampered = copy.deepcopy(first)
    lifecycle_tampered["lifecycle_state"] = "TERMINATED"
    assert verify_forward_evidence_bundle(lifecycle_tampered) is False


def test_lifecycle_review_and_manifest_apis_are_read_only(tmp_path: Path):
    store, trial_id = _observing_store(tmp_path / "market.sqlite")
    review_id, _ = _review(
        store, trial_id, "PAUSE_PAPER_OBSERVATION", 1, "Pause for API."
    )
    handler_type = make_handler(DashboardService(store), tmp_path)
    handler = object.__new__(handler_type)

    handler.path = f"/api/v1/forward-lifecycle?trial_id={trial_id}"
    status, lifecycle = handler._api_payload()
    assert status == HTTPStatus.OK
    assert lifecycle["current_state"] == "PAUSED"
    assert lifecycle["review_action_applies_parameters"] is False

    handler.path = f"/api/v1/forward-reviews/{review_id}"
    status, review = handler._api_payload()
    assert status == HTTPStatus.OK
    assert review["review"]["resulting_state"] == "PAUSED"
    assert review["live_execution_allowed"] is False

    handler.path = f"/api/v1/forward-evidence-manifest?trial_id={trial_id}"
    status, manifest = handler._api_payload()
    assert status == HTTPStatus.OK
    assert len(manifest["manifest"]["combined_sha256"]) == 64
    assert manifest["evidence_export_only"] is True
    assert "evidence" not in manifest


def test_review_and_export_clis_are_explicit_local_paths(tmp_path: Path):
    database = tmp_path / "market.sqlite"
    store, trial_id = _observing_store(database)
    root = Path(__file__).parents[1]
    review = subprocess.run(
        [
            sys.executable, str(root / "run_forward_review.py"),
            "--db", str(database), "--trial-id", trial_id,
            "--action", "PAUSE_PAPER_OBSERVATION",
            "--reviewer", "local-owner", "--note", "Pause from CLI.",
        ],
        check=True, capture_output=True, text=True,
    )
    assert "execution_mode=PAPER_ONLY" in review.stdout
    assert "review_action_applies_parameters=false" in review.stdout
    assert "live_execution_allowed=false" in review.stdout

    output = tmp_path / "evidence.json"
    exported = subprocess.run(
        [
            sys.executable, str(root / "run_forward_evidence_export.py"),
            "--db", str(database), "--trial-id", trial_id, "--output", str(output),
        ],
        check=True, capture_output=True, text=True,
    )
    assert "verified=true" in exported.stdout
    assert "evidence_export_only=true" in exported.stdout
    assert "live_execution_allowed=false" in exported.stdout
    assert verify_forward_evidence_bundle(json.loads(output.read_text(encoding="utf-8")))


def test_forward_lifecycle_ui_is_read_only_and_exposes_gates_and_export_trust():
    ui_root = Path(__file__).parents[1] / "ui"
    html = (ui_root / "index.html").read_text(encoding="utf-8")
    javascript = (ui_root / "app.js").read_text(encoding="utf-8")
    css = (ui_root / "styles.css").read_text(encoding="utf-8")
    assert "AARS // 03.19" in html
    assert 'id="forward-lifecycle-status"' in html
    assert 'id="forward-review-history"' in html
    assert 'id="forward-evidence-manifest"' in html
    assert "NO WEB REVIEW CONTROL" in html
    assert "TERMINATION IS IRREVERSIBLE" in html
    assert "/api/v1/forward-lifecycle?trial_id=${encodeURIComponent(latest.trial_id)}" in javascript
    assert "/api/v1/forward-evidence-manifest?trial_id=${encodeURIComponent(latest.trial_id)}" in javascript
    assert "/api/v1/forward-reviews/${encodeURIComponent(lifecycle.latest_review.review_id)}" in javascript
    assert "forward human review exceeded advisory authority" in javascript
    assert "THIS READ-ONLY SCREEN HAS NO REVIEW OR APPLY BUTTON" in javascript
    assert "run_forward_evidence_export.py" in javascript
    assert '.forward-lifecycle-heading > strong[data-status="TERMINATED"]' in css
