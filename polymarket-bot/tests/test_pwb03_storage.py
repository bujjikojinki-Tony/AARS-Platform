from uuid import uuid4

from backend.models.probability_governance import CalibrationResult
from backend.models.probability_governance import DisagreementLevel
from backend.models.probability_governance import EnginePromotionDecision
from backend.models.probability_governance import MarketOutcome
from backend.models.probability_governance import OutcomeStatus
from backend.models.probability_governance import ProbabilityComparisonView
from backend.models.probability_governance import ProbabilityEngineConfig
from backend.models.probability_governance import ProbabilityEngineRun
from backend.models.probability_governance import ProbabilityEngineType
from backend.models.probability_governance import PromotionDecisionType
from backend.storage.db import init_db
from backend.storage.repositories import Repository


def test_probability_governance_schema_and_defaults(tmp_path):
    db_path = tmp_path / "pwb03.sqlite"
    init_db(str(db_path))
    repo = Repository(str(db_path))

    engine_configs = repo.list_probability_engine_configs()
    assert [item["engine_id"] for item in engine_configs] == [
        "gaussian_v0",
        "deb_shadow_v0",
        "emos_shadow_v0",
    ]
    assert engine_configs[0]["engine_type"] == "PRIMARY"
    assert engine_configs[0]["enabled"] is True
    assert engine_configs[0]["can_be_primary"] is True
    assert engine_configs[1]["engine_type"] == "SHADOW"
    assert engine_configs[1]["can_be_primary"] is False
    assert engine_configs[2]["engine_type"] == "SHADOW"
    assert engine_configs[2]["can_be_primary"] is False

    config = ProbabilityEngineConfig(
        engine_id="custom_primary",
        engine_name="Custom Primary",
        engine_type=ProbabilityEngineType.PRIMARY,
        enabled=True,
        can_be_primary=True,
        description="Custom engine",
        default_params={"alpha": 1},
    )
    repo.save_probability_engine_config(config)
    fetched_config = repo.get_probability_engine_config("custom_primary")
    assert fetched_config is not None
    assert fetched_config["engine_id"] == "custom_primary"
    assert fetched_config["default_params"] == {"alpha": 1}


def test_probability_governance_repository_round_trip(tmp_path):
    db_path = tmp_path / "pwb03_round_trip.sqlite"
    init_db(str(db_path))
    repo = Repository(str(db_path))

    run = ProbabilityEngineRun(
        run_id=f"run_{uuid4().hex[:8]}",
        market_id="mock_weather_strong_yes",
        weather_view_id="wv_test",
        engine_id="gaussian_v0",
        engine_type=ProbabilityEngineType.PRIMARY,
        model_probability=0.684,
        expected_value=31.2,
        sigma=2.5,
        threshold=30.0,
        direction="ABOVE",
        params={"sigma": 2.5},
        warnings=[],
    )
    repo.save_probability_engine_run(run)

    comparison = ProbabilityComparisonView(
        comparison_id=f"cmp_{uuid4().hex[:8]}",
        market_id=run.market_id,
        weather_view_id=run.weather_view_id,
        active_engine_id="gaussian_v0",
        active_probability=0.684,
        engine_runs=[run],
        spread_between_engines=0.0,
        disagreement_level=DisagreementLevel.NONE,
        selection_reason="gaussian_v0 selected as active primary",
        warnings=["shadow engines are comparison only"],
    )
    repo.save_probability_comparison(comparison)

    outcome = MarketOutcome(
        outcome_id=f"out_{uuid4().hex[:8]}",
        market_id=run.market_id,
        resolved_value=31.8,
        resolved_direction_hit=True,
        official_source="manual_test",
        status=OutcomeStatus.RESOLVED,
        notes="Manual test outcome",
    )
    repo.save_market_outcome(outcome)

    calibration = CalibrationResult(
        calibration_id=f"cal_{uuid4().hex[:8]}",
        market_id=run.market_id,
        engine_id=run.engine_id,
        run_id=run.run_id,
        outcome_id=outcome.outcome_id,
        predicted_probability=0.684,
        actual_outcome=1,
        brier_score=(0.684 - 1) ** 2,
        absolute_error=abs(0.684 - 1),
        bucket="0.6-0.8",
    )
    repo.save_calibration_result(calibration)

    decision = EnginePromotionDecision(
        decision_id=f"pd_{uuid4().hex[:8]}",
        engine_id="deb_shadow_v0",
        current_type=ProbabilityEngineType.SHADOW,
        proposed_type=ProbabilityEngineType.SHADOW,
        eligible=False,
        decision=PromotionDecisionType.NEEDS_MORE_DATA,
        evidence_count=0,
        reason="insufficient calibration evidence",
    )
    repo.save_engine_promotion_decision(decision)

    runs = repo.list_probability_engine_runs_for_market(run.market_id)
    assert len(runs) == 1
    assert runs[0]["engine_id"] == "gaussian_v0"
    assert runs[0]["params"] == {"sigma": 2.5}

    comparison_row = repo.get_latest_probability_comparison(run.market_id)
    assert comparison_row is not None
    assert comparison_row["active_engine_id"] == "gaussian_v0"
    assert comparison_row["engine_runs"][0]["engine_id"] == "gaussian_v0"

    outcome_row = repo.get_latest_market_outcome(run.market_id)
    assert outcome_row is not None
    assert outcome_row["resolved_direction_hit"] is True

    calibration_rows = repo.list_calibration_results_for_engine("gaussian_v0")
    assert len(calibration_rows) == 1
    assert calibration_rows[0]["brier_score"] == (0.684 - 1) ** 2

    decision_row = repo.get_latest_engine_promotion_decision("deb_shadow_v0")
    assert decision_row is not None
    assert decision_row["decision"] == "NEEDS_MORE_DATA"
