from __future__ import annotations

from uuid import uuid4

from backend.models.command_review import CommandApprovalStatus
from backend.models.command_review import CommandGateStatus
from backend.models.command_review import CommandReviewRecord
from backend.models.command_review import CommandReviewStatus
from backend.models.command_review import CommandReviewRecommendation
from backend.models.core import ExecutionDecision
from backend.models.core import OpportunityCandidate
from backend.models.enums import ActionStatus
from backend.models.enums import ExecutionMode
from backend.models.enums import ExecutionStatus
from backend.models.enums import RiskStatus
from backend.models.enums import Side
from backend.models.execution_decision_review import ExecutionApprovalStatus
from backend.models.execution_decision_review import ExecutionDecisionReviewBundle
from backend.models.execution_decision_review import ExecutionDecisionReviewRecommendation
from backend.models.execution_decision_review import ExecutionDecisionReviewRecord
from backend.models.execution_decision_review import ExecutionDecisionReviewStatus
from backend.models.execution_decision_review import ExecutionDecisionReviewSummary
from backend.models.execution_decision_review import ExecutionGateStatus
from backend.storage.db import init_db
from backend.storage.repositories import Repository


def make_review(
    market_id: str = "mock_weather_strong_yes",
    *,
    review_status: ExecutionDecisionReviewStatus = ExecutionDecisionReviewStatus.READY,
    approval_status: ExecutionApprovalStatus = ExecutionApprovalStatus.PENDING,
    gate_status: ExecutionGateStatus = ExecutionGateStatus.WARN,
    recommendation: ExecutionDecisionReviewRecommendation = ExecutionDecisionReviewRecommendation.REVIEW_EXECUTION,
) -> ExecutionDecisionReviewRecord:
    return ExecutionDecisionReviewRecord(
        execution_decision_review_id=f"edr_{uuid4().hex[:10]}",
        market_id=market_id,
        decision_id=f"dec_{uuid4().hex[:10]}",
        candidate_id=f"cand_{uuid4().hex[:10]}",
        command_review_id="crv_001",
        shadow_evaluation_id="se_001",
        execution_mode=ExecutionMode.OBSERVE_ONLY.value,
        action="review",
        position_size=1.0,
        expected_cost=2.0,
        risk_status=RiskStatus.WARN.value,
        execution_status=ExecutionStatus.QUEUED.value,
        review_status=review_status,
        approval_status=approval_status,
        gate_status=gate_status,
        recommendation=recommendation,
        approval_window_valid=True,
        approval_valid_until="2026-06-01T00:00:00Z",
        raw_payload={"source": "test"},
        metadata={"case": "execution_decision_review"},
    )


def test_execution_decision_review_models_serialize():
    review = make_review()
    dumped = review.model_dump(mode="json")
    assert dumped["execution_decision_review_id"].startswith("edr_")
    assert dumped["market_id"] == "mock_weather_strong_yes"
    assert dumped["review_status"] == "READY"
    assert dumped["approval_status"] == "PENDING"
    assert dumped["gate_status"] == "WARN"
    assert dumped["recommendation"] == "REVIEW_EXECUTION"
    assert dumped["approval_window_valid"] is True


def test_execution_decision_review_tables_created(tmp_path):
    db_path = str(tmp_path / "execution_decision_review_tables.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    summary = repo.get_execution_decision_review_summary()
    assert isinstance(summary, ExecutionDecisionReviewSummary)
    assert summary.execution_decision_reviews == 0
    assert summary.unique_markets == 0
    assert summary.by_review_status == {}
    assert summary.by_approval_status == {}
    assert summary.by_gate_status == {}
    assert summary.by_execution_status == {}
    assert summary.by_execution_mode == {}
    assert summary.latest_reviewed_at is None


def test_execution_decision_review_save_list_bundle_summary(tmp_path):
    db_path = str(tmp_path / "execution_decision_review_repo.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    first = make_review(market_id="m1")
    second = make_review(
        market_id="m1",
        review_status=ExecutionDecisionReviewStatus.PENDING,
        approval_status=ExecutionApprovalStatus.APPROVED,
        gate_status=ExecutionGateStatus.ALLOW,
        recommendation=ExecutionDecisionReviewRecommendation.REQUEST_APPROVAL,
    )
    third = make_review(
        market_id="m2",
        review_status=ExecutionDecisionReviewStatus.BLOCKED,
        approval_status=ExecutionApprovalStatus.REJECTED,
        gate_status=ExecutionGateStatus.BLOCKED,
        recommendation=ExecutionDecisionReviewRecommendation.BLOCK,
    )
    repo.save_execution_decision_review_record(first)
    repo.save_execution_decision_review_record(second)
    repo.save_execution_decision_review_record(third)

    rows = repo.list_execution_decision_review_records(limit=10)
    assert len(rows) == 3
    assert rows[0]["execution_decision_review_id"] == third.execution_decision_review_id
    assert rows[0]["approval_window_valid"] is True

    latest = repo.get_latest_execution_decision_review_for_market("m1")
    assert latest is not None
    assert latest["market_id"] == "m1"
    assert latest["approval_status"] == "APPROVED"

    bundle = repo.get_execution_decision_review_bundle("m1")
    assert isinstance(bundle, ExecutionDecisionReviewBundle)
    assert bundle.market_id == "m1"
    assert len(bundle.execution_decision_reviews) == 2

    filtered = repo.list_execution_decision_review_records(
        market_id="m1",
        review_status=ExecutionDecisionReviewStatus.PENDING.value,
    )
    assert len(filtered) == 1
    assert filtered[0]["gate_status"] == "ALLOW"

    summary = repo.get_execution_decision_review_summary()
    assert summary.execution_decision_reviews == 3
    assert summary.unique_markets == 2
    assert summary.by_review_status["READY"] == 1
    assert summary.by_review_status["PENDING"] == 1
    assert summary.by_review_status["BLOCKED"] == 1
    assert summary.by_approval_status["PENDING"] == 1
    assert summary.by_approval_status["APPROVED"] == 1
    assert summary.by_approval_status["REJECTED"] == 1
    assert summary.by_gate_status["WARN"] == 1
    assert summary.by_gate_status["ALLOW"] == 1
    assert summary.by_gate_status["BLOCKED"] == 1
    assert summary.latest_reviewed_at is not None


def test_latest_execution_decision_lookup_joins_candidate(tmp_path):
    db_path = str(tmp_path / "execution_decision_lookup.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    candidate = OpportunityCandidate(
        candidate_id="cand_latest_1",
        signal_id="sig_001",
        market_id="m1",
        question="Will Tokyo high temperature exceed 30C on June 1?",
        side=Side.YES,
        market_probability=0.5,
        model_probability=0.61,
        edge_percent=0.11,
        liquidity=1000,
        spread=0.03,
        confidence_tier="HIGH",
        risk_status=RiskStatus.WARN,
        action_status=ActionStatus.WATCH,
    )
    repo.save_opportunity_candidate(candidate)
    decision = ExecutionDecision(
        decision_id="dec_latest_1",
        candidate_id="cand_latest_1",
        mode=ExecutionMode.OBSERVE_ONLY,
        action="review",
        position_size=1.0,
        expected_cost=1.0,
        risk_status=RiskStatus.WARN,
        execution_status=ExecutionStatus.QUEUED,
    )
    repo.save_execution_decision(decision)

    latest = repo.get_latest_execution_decision_for_market("m1")
    assert latest is not None
    assert latest["decision_id"] == "dec_latest_1"
