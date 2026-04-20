from __future__ import annotations

from weather_telegram_console.integrations.intent_writer import IntentWriter


def test_find_pending_by_signal_id(tmp_path) -> None:
    writer = IntentWriter(output_dir=str(tmp_path))

    payload = {
        "intent_id": "intent_001",
        "market_id": "sample_market_001",
        "signal_id": "sig_001",
        "side": "buy",
        "price": 0.42,
        "size": 10,
        "post_only": True,
        "max_slippage_pct": 0.02,
        "approved": True,
    }

    writer.write(payload)

    found = writer.find_pending_by_signal_id("sig_001")
    assert found is not None
    assert found.name == "intent_001.json"


def test_build_small_intent_contains_execution_contract(tmp_path) -> None:
    writer = IntentWriter(output_dir=str(tmp_path))
    payload = writer.build_small_intent(
        signal_payload={
            "signal_id": "sig_abc",
            "market_id": "sample_market_001",
            "probability_contract": {
                "contract_version": "probability_contract.v1",
                "probability_mode": "heuristic_not_calibrated",
                "calibration_status": "not_calibrated",
                "execution_constraint": "manual_advisory_only",
            },
        }
    )

    assert payload["schema_version"] == "execution_intent.v1"
    assert payload["decision_ref"].startswith("decision_telegram_")
    assert payload["authorization_ref"] == "approval_required"
    assert payload["contract_version"] == "probability_contract.v1"
