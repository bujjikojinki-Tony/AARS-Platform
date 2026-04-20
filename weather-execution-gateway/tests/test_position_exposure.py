import json

from typer.testing import CliRunner

from weather_execution_gateway import main as gateway_main
from weather_execution_gateway.models.order_intent import OrderIntent
from weather_execution_gateway.risk.position_exposure import PositionExposureReader


def test_position_exposure_reader_computes_market_and_total_notional(tmp_path):
    path = tmp_path / "position_snapshot.json"
    path.write_text(
        json.dumps(
            {
                "updated_at": "2026-04-18T00:00:00+00:00",
                "balance": {
                    "available_balance": 100.0,
                    "total_balance": 125.0,
                    "currency": "USDC",
                    "manual_order_only": True,
                    "snapshot_available": True,
                },
                "positions": [
                    {
                        "market_id": "market_a",
                        "size": 100,
                        "current_price": 0.40,
                    },
                    {
                        "market_id": "market_b",
                        "notional": 12.5,
                    },
                ],
                "open_orders": [
                    {
                        "market_id": "market_a",
                        "price": 0.50,
                        "remaining_size": 10,
                    },
                    {
                        "market_id": "market_c",
                        "notional": 7.0,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    exposure = PositionExposureReader(path).exposure_for_market("market_a")

    assert exposure["snapshot_available"] is True
    assert exposure["market_position_notional"] == 40.0
    assert exposure["market_open_order_notional"] == 5.0
    assert exposure["market_notional"] == 45.0
    assert exposure["total_position_notional"] == 52.5
    assert exposure["total_open_order_notional"] == 12.0
    assert exposure["total_notional"] == 64.5
    assert exposure["market_position_count"] == 1
    assert exposure["market_open_order_count"] == 1
    assert exposure["total_position_count"] == 2
    assert exposure["total_open_order_count"] == 2
    assert exposure["available_balance"] == 100.0
    assert exposure["total_balance"] == 125.0
    assert exposure["manual_order_only"] is True


def test_dry_run_uses_position_snapshot_for_exposure_limits(tmp_path):
    position_path = tmp_path / "position_snapshot.json"
    position_path.write_text(
        json.dumps(
            {
                "updated_at": "2026-04-18T00:00:00+00:00",
                "positions": [
                    {
                        "market_id": "sample_market_001",
                        "notional": 90.0,
                    }
                ],
                "open_orders": [
                    {
                        "market_id": "sample_market_001",
                        "notional": 8.0,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    intent = OrderIntent(
        schema_version="execution_intent.v1",
        intent_id="intent_1",
        market_id="sample_market_001",
        signal_id="sig_intent_1",
        decision_ref="decision_intent_1",
        authorization_ref="approval_intent_1",
        side="buy",
        price=0.50,
        size=10,
        approved=True,
    )

    executed, risk_state = gateway_main._run_dry_run_for_intent(
        intent=intent,
        risk_cfg={
            "execution": {"enabled": True},
            "exposure": {"max_notional_per_market": 100, "max_total_notional": 500},
        },
        whitelist_cfg={"markets": ["sample_market_001"]},
        approval_valid=True,
        position_snapshot_path=position_path,
    )

    assert executed.accepted is False
    assert executed.status == "blocked"
    assert risk_state.reason == "exposure_limit_exceeded"
    assert risk_state.market_notional == 98.0
    assert risk_state.new_order_notional == 5.0


def test_dry_run_uses_gate_stack_api_when_unified_status_missing(tmp_path):
    gate_stack_api_path = tmp_path / "gate_stack_api.json"
    gate_stack_api_path.write_text(
        json.dumps(
            {
                "schema_version": "gate_stack_api.v1",
                "market_gate_views": [
                    {
                        "market_id": "sample_market_001",
                        "data_gate": "pass",
                        "data_gate_reasons": [],
                        "resolver_gate": "blocked",
                        "resolver_gate_reasons": ["resolver_not_matched"],
                        "probability_gate": "pass",
                        "probability_gate_reasons": [],
                        "freshness_gate": "pass",
                        "freshness_gate_reasons": [],
                        "authorization_gate": "blocked",
                        "authorization_gate_reasons": ["resolver_not_matched"],
                        "execution_gate": "pass",
                        "execution_gate_reasons": [],
                        "block_reasons": ["resolver_not_matched"],
                    }
                ],
                "gate_stack": {
                    "authorization_gate": "pass",
                    "execution_gate": "pass",
                    "block_reasons": [],
                },
                "block_reasons": [],
            }
        ),
        encoding="utf-8",
    )
    intent = OrderIntent(
        schema_version="execution_intent.v1",
        intent_id="intent_gate_stack_api",
        market_id="sample_market_001",
        signal_id="sig_gate_stack_api",
        decision_ref="decision_gate_stack_api",
        authorization_ref="approval_gate_stack_api",
        side="buy",
        price=0.5,
        size=10,
        approved=True,
        probability_mode="live_approved",
        execution_constraint="live_execution_allowed",
        calibration_status="calibrated",
        contract_version="probability_contract.v1",
        probability_contract={
            "contract_version": "probability_contract.v1",
            "probability_mode": "live_approved",
            "execution_constraint": "live_execution_allowed",
            "calibration_status": "calibrated",
        },
    )

    executed, risk_state = gateway_main._run_dry_run_for_intent(
        intent=intent,
        risk_cfg={
            "execution": {"enabled": True},
            "exposure": {"max_notional_per_market": 200, "max_total_notional": 500},
        },
        whitelist_cfg={"markets": ["sample_market_001"]},
        approval_valid=True,
        unified_status_path=tmp_path / "missing_unified_status.json",
        gate_stack_api_path=gate_stack_api_path,
    )

    assert executed.accepted is False
    assert executed.status == "blocked"
    assert risk_state.reason == "resolver_not_matched"


def test_dry_run_prefers_gate_stack_api_over_unified_status(tmp_path):
    unified_status_path = tmp_path / "unified_status.json"
    unified_status_path.write_text(
        json.dumps(
            {
                "schema_version": "unified_status.v1",
                "current_market": {"market_id": "sample_market_001"},
                "gate_stack": {
                    "authorization_gate": "pass",
                    "execution_gate": "pass",
                    "block_reasons": [],
                },
                "block_reasons": [],
            }
        ),
        encoding="utf-8",
    )
    gate_stack_api_path = tmp_path / "gate_stack_api.json"
    gate_stack_api_path.write_text(
        json.dumps(
            {
                "schema_version": "gate_stack_api.v1",
                "market_gate_views": [
                    {
                        "market_id": "sample_market_001",
                        "resolver_gate": "blocked",
                        "resolver_gate_reasons": ["resolver_not_matched"],
                        "authorization_gate": "blocked",
                        "execution_gate": "blocked",
                        "block_reasons": ["resolver_not_matched"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    intent = OrderIntent(
        schema_version="execution_intent.v1",
        intent_id="intent_pref_api",
        market_id="sample_market_001",
        signal_id="sig_pref_api",
        decision_ref="decision_pref_api",
        authorization_ref="approval_pref_api",
        side="buy",
        price=0.5,
        size=10,
        approved=True,
        probability_mode="live_approved",
        execution_constraint="live_execution_allowed",
        calibration_status="calibrated",
        contract_version="probability_contract.v1",
        probability_contract={
            "contract_version": "probability_contract.v1",
            "probability_mode": "live_approved",
            "execution_constraint": "live_execution_allowed",
            "calibration_status": "calibrated",
        },
    )

    executed, risk_state = gateway_main._run_dry_run_for_intent(
        intent=intent,
        risk_cfg={
            "execution": {"enabled": True},
            "exposure": {"max_notional_per_market": 200, "max_total_notional": 500},
        },
        whitelist_cfg={"markets": ["sample_market_001"]},
        approval_valid=True,
        unified_status_path=unified_status_path,
        gate_stack_api_path=gate_stack_api_path,
    )

    assert executed.accepted is False
    assert executed.status == "blocked"
    assert risk_state.reason == "resolver_not_matched"


def test_export_gate_runtime_snapshot_cli(monkeypatch, tmp_path):
    gate_stack_api_path = tmp_path / "gate_stack_api.json"
    gate_stack_api_path.write_text(
        json.dumps(
            {
                "schema_version": "gate_stack_api.v1",
                "source_schema_version": "unified_status.v1",
                "market_id": "sample_market_001",
                "promotion_state": {
                    "schema_version": "promotion_state.v1",
                    "probability_mode": "shadow_calibrated_candidate",
                    "base_probability_mode": "heuristic_not_calibrated",
                    "execution_constraint": "dry_run_only",
                    "base_execution_constraint": "manual_advisory_only",
                    "promotion_reason": "candidate_thresholds_passed",
                },
                "market_gate_views": [
                    {
                        "market_id": "sample_market_001",
                        "authorization_gate": "blocked",
                        "execution_gate": "blocked",
                        "block_reasons": ["resolver_not_matched"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    out_path = tmp_path / "gateway_gate_runtime_snapshot.json"
    monkeypatch.setattr(gateway_main, "GATE_STACK_API_PATH", gate_stack_api_path)
    monkeypatch.setattr(gateway_main, "UNIFIED_STATUS_PATH", tmp_path / "missing_unified_status.json")
    monkeypatch.setattr(gateway_main, "GATEWAY_GATE_RUNTIME_SNAPSHOT_JSON", out_path)

    result = CliRunner().invoke(
        gateway_main.app,
        ["export-gate-runtime-snapshot", "--market-id", "sample_market_001"],
    )
    assert result.exit_code == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "gateway_gate_runtime_snapshot.v1"
    assert payload["gate_source"] == "api"
    assert payload["source_schema_version"] == "unified_status.v1"
    assert payload["promotion_state"]["probability_mode"] == "shadow_calibrated_candidate"
