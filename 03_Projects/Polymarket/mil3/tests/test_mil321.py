from __future__ import annotations

import copy
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from pathlib import Path

import pytest

from aars_market.activation_approval import (
    build_isolated_activation_review,
    build_isolated_activation_revocation,
)
from aars_market.api import make_handler
from aars_market.evidence_export import write_forward_evidence_bundle
from aars_market.evidence_offline import build_offline_verification_report
from aars_market.isolated_config import (
    build_isolated_configuration,
    build_sandbox_event,
    canonical_sha256,
)
from aars_market.service import DashboardService
from tests.test_mil316 import START
from tests.test_mil320 import _confirmed_bundle, _exported_bundle


def _approved_store(
    tmp_path: Path,
    monkeypatch,
    *,
    validity_hours: int = 48,
    approved_at: datetime = START,
):
    store, trial_id, base, path, _ = _exported_bundle(tmp_path)
    confirmed = _confirmed_bundle(base)
    path.unlink()
    write_forward_evidence_bundle(confirmed, path)
    report = build_offline_verification_report(path, checked_at=START)
    monkeypatch.setattr(
        "aars_market.evidence_export.build_forward_evidence_bundle",
        lambda selected_store, selected_trial_id: confirmed,
    )
    approval = build_isolated_activation_review(
        store,
        confirmed,
        report,
        action="APPROVE_ISOLATED_PAPER_ACTIVATION",
        reviewer="owner",
        note="Approve isolated registry only.",
        sandbox_id="paper-sandbox",
        reviewed_at=approved_at,
        validity_hours=validity_hours,
    )
    approval_id = store.archive_isolated_activation_review(approval)
    return store, trial_id, approval_id


def _registered_store(tmp_path: Path, monkeypatch, *, validity_hours: int = 48):
    store, trial_id, approval_id = _approved_store(
        tmp_path, monkeypatch, validity_hours=validity_hours
    )
    payload = build_isolated_configuration(
        store, trial_id, registered_at=START + timedelta(minutes=1)
    )
    configuration_id = store.archive_isolated_paper_configuration(payload)
    return store, trial_id, approval_id, configuration_id, payload


def test_registry_consumes_approval_once_and_keeps_entry_inert(tmp_path: Path, monkeypatch):
    store, trial_id, approval_id, configuration_id, payload = _registered_store(
        tmp_path, monkeypatch
    )
    assert payload["approval_review_id"] == approval_id
    assert payload["authority"]["registry_entry_inert"] is True
    assert payload["authority"]["live_execution_allowed"] is False
    assert store.get_isolated_paper_configuration(configuration_id) == payload
    assert store.resolve_isolated_paper_sandbox("paper-sandbox", now=START)[
        "effective_state"
    ] == "EMPTY"

    retry = build_isolated_configuration(
        store, trial_id, registered_at=START + timedelta(minutes=2)
    )
    assert retry["configuration_id"] == configuration_id
    assert store.archive_isolated_paper_configuration(retry) == configuration_id
    assert len(store.list_isolated_paper_configurations()) == 1

    tampered = copy.deepcopy(payload)
    tampered["configuration"]["settings"]["fee_rate"] = 0.99
    tampered["configuration_sha256"] = canonical_sha256(tampered["configuration"])
    with pytest.raises(ValueError, match="identity is invalid"):
        store.archive_isolated_paper_configuration(tampered)


def test_activation_is_atomic_and_rejects_stale_optimistic_event(tmp_path: Path, monkeypatch):
    store, _, _, configuration_id, _ = _registered_store(tmp_path, monkeypatch)
    first = build_sandbox_event(
        store,
        "paper-sandbox",
        action="ACTIVATE",
        configuration_id=configuration_id,
        operator="owner",
        note="Activate isolated pointer only.",
        event_at=START + timedelta(hours=1),
    )
    stale = build_sandbox_event(
        store,
        "paper-sandbox",
        action="ACTIVATE",
        configuration_id=configuration_id,
        operator="second-owner",
        note="Stale concurrent activation.",
        event_at=START + timedelta(hours=1, minutes=1),
    )
    event_id = store.archive_isolated_paper_sandbox_event(first)
    view = store.resolve_isolated_paper_sandbox(
        "paper-sandbox", now=START + timedelta(hours=2)
    )
    assert view["effective_state"] == "ACTIVE"
    assert view["stored_configuration_id"] == configuration_id
    assert view["effective_configuration_id"] == configuration_id
    assert view["state_version"] == 1
    assert view["latest_event_id"] == event_id
    assert view["starts_strategy_process"] is False
    backdated = build_sandbox_event(
        store,
        "paper-sandbox",
        action="ROLLBACK",
        configuration_id=None,
        operator="owner",
        note="Backdated rollback.",
        event_at=START + timedelta(minutes=30),
    )
    with pytest.raises(ValueError, match="event time must advance"):
        store.archive_isolated_paper_sandbox_event(backdated)
    with pytest.raises(ValueError, match="state changed before commit"):
        store.archive_isolated_paper_sandbox_event(stale)
    assert store.resolve_isolated_paper_sandbox("paper-sandbox")["state_version"] == 1


def test_atomic_rollback_clears_first_activation_and_is_one_time(tmp_path: Path, monkeypatch):
    store, _, _, configuration_id, _ = _registered_store(tmp_path, monkeypatch)
    activation = build_sandbox_event(
        store, "paper-sandbox", action="ACTIVATE",
        configuration_id=configuration_id, operator="owner", note="Activate.",
        event_at=START + timedelta(hours=1),
    )
    activation_id = store.archive_isolated_paper_sandbox_event(activation)
    rollback = build_sandbox_event(
        store, "paper-sandbox", action="ROLLBACK",
        configuration_id=None, operator="owner", note="Rollback to empty baseline.",
        event_at=START + timedelta(hours=2),
    )
    assert rollback["rollback_of_event_id"] == activation_id
    assert rollback["next_configuration_id"] is None
    store.archive_isolated_paper_sandbox_event(rollback)
    view = store.resolve_isolated_paper_sandbox(
        "paper-sandbox", now=START + timedelta(hours=3)
    )
    assert view["effective_state"] == "EMPTY"
    assert view["stored_configuration_id"] is None
    assert view["state_version"] == 2
    with pytest.raises(ValueError, match="no unrolled activation"):
        build_sandbox_event(
            store, "paper-sandbox", action="ROLLBACK",
            configuration_id=None, operator="owner", note="Repeat rollback.",
            event_at=START + timedelta(hours=3),
        )


def test_expiry_is_immediate_on_read_and_reconciliation_persists_invalidation(
    tmp_path: Path, monkeypatch
):
    store, _, _, configuration_id, _ = _registered_store(
        tmp_path, monkeypatch, validity_hours=2
    )
    event = build_sandbox_event(
        store, "paper-sandbox", action="ACTIVATE",
        configuration_id=configuration_id, operator="owner", note="Activate briefly.",
        event_at=START + timedelta(hours=1),
    )
    store.archive_isolated_paper_sandbox_event(event)
    before_events = store.list_isolated_paper_sandbox_events("paper-sandbox")
    expired = store.resolve_isolated_paper_sandbox(
        "paper-sandbox", now=START + timedelta(hours=3)
    )
    assert expired["effective_state"] == "EXPIRED_FAIL_SAFE"
    assert expired["stored_configuration_id"] == configuration_id
    assert expired["effective_configuration_id"] is None
    assert store.list_isolated_paper_sandbox_events("paper-sandbox") == before_events

    summary = store.reconcile_isolated_paper_sandboxes(
        now=START + timedelta(hours=3)
    )
    assert summary["records"][0]["status"] == "INVALIDATED"
    reconciled = store.resolve_isolated_paper_sandbox(
        "paper-sandbox", now=START + timedelta(hours=3)
    )
    assert reconciled["effective_state"] == "EMPTY"
    assert reconciled["stored_configuration_id"] is None
    assert len(store.list_isolated_paper_sandbox_events("paper-sandbox")) == 2


def test_revocation_immediately_suppresses_effective_configuration(tmp_path: Path, monkeypatch):
    store, trial_id, _, configuration_id, _ = _registered_store(tmp_path, monkeypatch)
    activation = build_sandbox_event(
        store, "paper-sandbox", action="ACTIVATE",
        configuration_id=configuration_id, operator="owner", note="Activate.",
        event_at=START + timedelta(hours=1),
    )
    store.archive_isolated_paper_sandbox_event(activation)
    revocation = build_isolated_activation_revocation(
        store,
        trial_id,
        reviewer="owner",
        note="Revoke active isolated authority.",
        reviewed_at=START + timedelta(hours=2),
    )
    store.archive_isolated_activation_review(revocation)
    view = store.resolve_isolated_paper_sandbox(
        "paper-sandbox", now=START + timedelta(hours=3)
    )
    assert view["effective_state"] == "REVOKED_FAIL_SAFE"
    assert view["effective_configuration"] is None
    summary = store.reconcile_isolated_paper_sandboxes(
        now=START + timedelta(hours=3)
    )
    assert summary["records"][0]["reason"] == "REVOKED_FAIL_SAFE"


def test_activation_rejects_expired_wrong_sandbox_and_backdated_events(
    tmp_path: Path, monkeypatch
):
    store, _, _, configuration_id, _ = _registered_store(
        tmp_path, monkeypatch, validity_hours=2
    )
    expired = build_sandbox_event(
        store, "paper-sandbox", action="ACTIVATE",
        configuration_id=configuration_id, operator="owner", note="Too late.",
        event_at=START + timedelta(hours=3),
    )
    with pytest.raises(ValueError, match="APPROVAL_EXPIRED"):
        store.archive_isolated_paper_sandbox_event(expired)
    wrong = build_sandbox_event(
        store, "another-sandbox", action="ACTIVATE",
        configuration_id=configuration_id, operator="owner", note="Wrong sandbox.",
        event_at=START + timedelta(hours=1),
    )
    with pytest.raises(ValueError, match="another sandbox"):
        store.archive_isolated_paper_sandbox_event(wrong)


def test_registry_and_sandbox_apis_remain_read_only(tmp_path: Path, monkeypatch):
    store, _, _, configuration_id, _ = _registered_store(tmp_path, monkeypatch)
    event = build_sandbox_event(
        store, "paper-sandbox", action="ACTIVATE",
        configuration_id=configuration_id, operator="owner", note="Activate for API.",
        event_at=START + timedelta(hours=1),
    )
    event_id = store.archive_isolated_paper_sandbox_event(event)
    handler_type = make_handler(DashboardService(store), tmp_path)
    handler = object.__new__(handler_type)

    handler.path = "/api/v1/isolated-configurations?sandbox_id=paper-sandbox"
    status, index = handler._api_payload()
    assert status == HTTPStatus.OK
    assert index["configurations"][0]["configuration_id"] == configuration_id
    assert index["registry_entries_inert"] is True
    handler.path = f"/api/v1/isolated-configurations/{configuration_id}"
    status, detail = handler._api_payload()
    assert status == HTTPStatus.OK
    assert detail["starts_strategy_process"] is False
    handler.path = "/api/v1/isolated-sandbox?sandbox_id=paper-sandbox"
    status, sandbox = handler._api_payload()
    assert status == HTTPStatus.OK
    assert sandbox["effective_state"] == "EXPIRED_FAIL_SAFE"  # current wall time is later
    assert sandbox["effective_configuration_id"] is None
    handler.path = "/api/v1/isolated-sandbox-events?sandbox_id=paper-sandbox"
    status, events = handler._api_payload()
    assert status == HTTPStatus.OK
    assert events["events"][0]["event_id"] == event_id
    handler.path = f"/api/v1/isolated-sandbox-events/{event_id}"
    status, event_detail = handler._api_payload()
    assert status == HTTPStatus.OK
    assert event_detail["live_execution_allowed"] is False


def test_registry_activate_rollback_and_reconcile_cli_are_explicit(tmp_path: Path, monkeypatch):
    store, trial_id, _ = _approved_store(
        tmp_path,
        monkeypatch,
        validity_hours=48,
        approved_at=datetime.now(timezone.utc),
    )
    root = Path(__file__).parents[1]
    registered = subprocess.run(
        [sys.executable, str(root / "run_isolated_paper_config.py"),
         "--db", store.path, "--action", "REGISTER", "--trial-id", trial_id],
        check=True, capture_output=True, text=True,
    )
    configuration_id = registered.stdout.split("configuration_id=", 1)[1].split()[0]
    assert "registry_entry_inert=true" in registered.stdout
    activated = subprocess.run(
        [sys.executable, str(root / "run_isolated_paper_config.py"),
         "--db", store.path, "--action", "ACTIVATE",
         "--configuration-id", configuration_id, "--sandbox-id", "paper-sandbox",
         "--operator", "owner", "--note", "Activate CLI pointer."],
        check=True, capture_output=True, text=True,
    )
    assert "starts_strategy_process=false" in activated.stdout
    assert "live_execution_allowed=false" in activated.stdout
    rolled_back = subprocess.run(
        [sys.executable, str(root / "run_isolated_paper_config.py"),
         "--db", store.path, "--action", "ROLLBACK",
         "--sandbox-id", "paper-sandbox", "--operator", "owner",
         "--note", "Rollback CLI pointer."],
        check=True, capture_output=True, text=True,
    )
    assert "stored_configuration_id=EMPTY" in rolled_back.stdout
    reconciled = subprocess.run(
        [sys.executable, str(root / "run_isolated_paper_config.py"),
         "--db", store.path, "--action", "RECONCILE"],
        check=True, capture_output=True, text=True,
    )
    assert '"configuration_process_started": false' in reconciled.stdout
    assert "live_execution_allowed=false" in reconciled.stdout


def test_mil321_ui_separates_stored_pointer_effective_state_and_rollback_gate():
    ui_root = Path(__file__).parents[1] / "ui"
    html = (ui_root / "index.html").read_text(encoding="utf-8")
    javascript = (ui_root / "app.js").read_text(encoding="utf-8")
    css = (ui_root / "styles.css").read_text(encoding="utf-8")
    assert "AARS // 03.23" in html
    assert 'id="sandbox-effective-status"' in html
    assert 'id="sandbox-pointer-summary"' in html
    assert 'id="sandbox-configuration-detail"' in html
    assert 'id="sandbox-rollback-status"' in html
    assert 'id="sandbox-event-history"' in html
    assert "NO STRATEGY PROCESS STARTED" in html
    assert "/api/v1/isolated-configurations?sandbox_id=${encodeURIComponent(sandboxId)}" in javascript
    assert "/api/v1/isolated-sandbox?sandbox_id=${encodeURIComponent(sandboxId)}" in javascript
    assert "/api/v1/isolated-sandbox-events?sandbox_id=${encodeURIComponent(sandboxId)}" in javascript
    assert "isolated sandbox effective configuration differs from fail-safe state" in javascript
    assert "STORED POINTER" in javascript
    assert "EFFECTIVE CONFIG" in javascript
    assert "THIS SCREEN HAS NO REGISTER, ACTIVATE OR ROLLBACK BUTTON" in javascript
    assert '.forward-lifecycle-heading > strong[data-status$="FAIL_SAFE"]' in css
    assert ".isolated-registry-grid" in css
