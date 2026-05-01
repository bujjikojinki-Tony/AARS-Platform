from __future__ import annotations

from uuid import uuid4

from backend.models.execution_queue_review import ExecutionQueueApprovalStatus
from backend.models.execution_queue_review import ExecutionQueueGateStatus
from backend.models.execution_queue_review import ExecutionQueueReviewBundle
from backend.models.execution_queue_review import ExecutionQueueReviewRecommendation
from backend.models.execution_queue_review import ExecutionQueueReviewRecord
from backend.models.execution_queue_review import ExecutionQueueReviewStatus
from backend.models.execution_queue_review import ExecutionQueueReviewSummary
from backend.storage.db import init_db
from backend.storage.repositories import Repository


def make_review(
    market_id: str = "mock_weather_strong_yes",
    *,
    review_status: ExecutionQueueReviewStatus = ExecutionQueueReviewStatus.READY,
    approval_status: ExecutionQueueApprovalStatus = ExecutionQueueApprovalStatus.PENDING,
    gate_status: ExecutionQueueGateStatus = ExecutionQueueGateStatus.WARN,
    recommendation: ExecutionQueueReviewRecommendation = ExecutionQueueReviewRecommendation.REVIEW_EXECUTION,
) -> ExecutionQueueReviewRecord:
    return ExecutionQueueReviewRecord(
        execution_queue_review_id=f"eqr_{uuid4().hex[:10]}",
        market_id=market_id,
        decision_id=f"dec_{uuid4().hex[:10]}",
        candidate_id=f"cand_{uuid4().hex[:10]}",
        command_review_id="crv_001",
        execution_decision_review_id="edr_001",
        shadow_evaluation_id="see_001",
        execution_mode="OBSERVE_ONLY",
        action="review",
        position_size=1.0,
        expected_cost=2.0,
        risk_status="WARN",
        execution_status="QUEUED",
        review_status=review_status,
        approval_status=approval_status,
        gate_status=gate_status,
        recommendation=recommendation,
        approval_window_valid=True,
        approval_valid_until="2026-06-01T00:00:00Z",
        raw_payload={"source": "test"},
        metadata={"case": "execution_queue_review"},
    )


def test_execution_queue_review_models_serialize() -> None:
    review = make_review()
    dumped = review.model_dump(mode="json")

    assert dumped["execution_queue_review_id"].startswith("eqr_")
    assert dumped["market_id"] == "mock_weather_strong_yes"
    assert dumped["review_status"] == "READY"
    assert dumped["approval_status"] == "PENDING"
    assert dumped["gate_status"] == "WARN"
    assert dumped["recommendation"] == "REVIEW_EXECUTION"
    assert dumped["approval_window_valid"] is True


def test_execution_queue_review_tables_created(tmp_path) -> None:
    db_path = str(tmp_path / "execution_queue_review_tables.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    summary = repo.get_execution_queue_review_summary()

    assert isinstance(summary, ExecutionQueueReviewSummary)
    assert summary.execution_queue_reviews == 0
    assert summary.unique_markets == 0
    assert summary.by_review_status == {}
    assert summary.by_approval_status == {}
    assert summary.by_gate_status == {}
    assert summary.by_execution_status == {}
    assert summary.by_execution_mode == {}
    assert summary.latest_reviewed_at is None


def test_execution_queue_review_save_list_bundle_summary(tmp_path) -> None:
    db_path = str(tmp_path / "execution_queue_review_repo.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    first = make_review(market_id="m1")
    second = make_review(
        market_id="m1",
        review_status=ExecutionQueueReviewStatus.PENDING,
        approval_status=ExecutionQueueApprovalStatus.APPROVED,
        gate_status=ExecutionQueueGateStatus.ALLOW,
        recommendation=ExecutionQueueReviewRecommendation.REQUEST_APPROVAL,
    )
    third = make_review(
        market_id="m2",
        review_status=ExecutionQueueReviewStatus.BLOCKED,
        approval_status=ExecutionQueueApprovalStatus.REJECTED,
        gate_status=ExecutionQueueGateStatus.BLOCKED,
        recommendation=ExecutionQueueReviewRecommendation.BLOCK,
    )
    repo.save_execution_queue_review_record(first)
    repo.save_execution_queue_review_record(second)
    repo.save_execution_queue_review_record(third)

    rows = repo.list_execution_queue_review_records(limit=10)
    assert len(rows) == 3
    assert rows[0]["execution_queue_review_id"] == third.execution_queue_review_id
    assert rows[0]["approval_window_valid"] is True

    latest = repo.get_latest_execution_queue_review_for_market("m1")
    assert latest is not None
    assert latest["market_id"] == "m1"
    assert latest["approval_status"] == "APPROVED"

    bundle = repo.get_execution_queue_review_bundle("m1")
    assert isinstance(bundle, ExecutionQueueReviewBundle)
    assert bundle.market_id == "m1"
    assert len(bundle.execution_queue_reviews) == 2

    filtered = repo.list_execution_queue_review_records(
        market_id="m1",
        review_status=ExecutionQueueReviewStatus.PENDING.value,
    )
    assert len(filtered) == 1
    assert filtered[0]["gate_status"] == "ALLOW"

    summary = repo.get_execution_queue_review_summary()
    assert summary.execution_queue_reviews == 3
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
