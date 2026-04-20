from weather_comparison_engine.schemas.probability_contract import build_probability_contract
from weather_comparison_engine.schemas.probability_state import ProbabilityState


def test_probability_state_embeds_probability_contract() -> None:
    state = ProbabilityState(
        market_id="m1",
        timestamp="2026-04-19T00:00:00+00:00",
        probability_mode="shadow_calibrated_candidate",
        calibration_status="candidate",
        execution_constraint="dry_run_only",
        validation_report_generated_at="2026-04-19T00:00:00+00:00",
    )

    assert state.contract_version == "probability_contract.v1"
    assert state.probability_contract["contract_version"] == "probability_contract.v1"
    assert state.probability_contract["probability_mode"] == "shadow_calibrated_candidate"
    assert state.probability_contract["execution_constraint"] == "dry_run_only"
    assert state.probability_contract["validation_ref"] == "2026-04-19T00:00:00+00:00"


def test_build_probability_contract_defaults_to_manual_advisory() -> None:
    contract = build_probability_contract({})

    assert contract["contract_version"] == "probability_contract.v1"
    assert contract["probability_mode"] == "heuristic_not_calibrated"
    assert contract["calibration_status"] == "not_calibrated"
    assert contract["execution_constraint"] == "manual_advisory_only"
