from __future__ import annotations

from uuid import uuid4

from backend.models.approval_window_review import ApprovalWindowRecommendation
from backend.models.approval_window_review import ApprovalWindowReviewBundle
from backend.models.approval_window_review import ApprovalWindowReviewRecord
from backend.models.approval_window_review import ApprovalWindowReviewStatus
from backend.models.approval_window_review import ApprovalWindowReviewSummary
from backend.models.approval_window_review import ApprovalWindowState
from backend.storage.db import init_db
from backend.storage.repositories import Repository


def make_review(
    market_id: str = "mock_weather_strong_yes",
    *,
    review_status: ApprovalWindowReviewStatus = ApprovalWindowReviewStatus.READY,
    window_state: ApprovalWindowState = ApprovalWindowState.OPEN,
    recommendation: ApprovalWindowRecommendation = ApprovalWindowRecommendation.REVIEW_WINDOW,
) -> ApprovalWindowReviewRecord:
    return ApprovalWindowReviewRecord(
        approval_window_review_id=f"awr_{uuid4().hex[:10]}",
        market_id=market_id,
        decision_id=f"dec_{uuid4().hex[:10]}",
        candidate_id=f"cand_{uuid4().hex[:10]}",
        command_review_id="crv_001",
        execution_decision_review_id="edr_001",
        execution_queue_review_id="eqr_001",
        approval_status="PENDING",
        approval_window_valid=True,
        approval_valid_until="2026-06-01T00:00:00Z",
        review_status=review_status,
        window_state=window_state,
        recommendation=recommendation,
        raw_payload={"source": "test"},
        metadata={"case": "approval_window_review"},
    )


def test_approval_window_review_models_serialize() -> None:
    review = make_review()
    dumped = review.model_dump(mode="json")

    assert dumped["approval_window_review_id"].startswith("awr_")
    assert dumped["market_id"] == "mock_weather_strong_yes"
    assert dumped["review_status"] == "READY"
    assert dumped["window_state"] == "OPEN"
    assert dumped["recommendation"] == "REVIEW_WINDOW"
    assert dumped["approval_window_valid"] is True


def test_approval_window_review_tables_created(tmp_path) -> None:
    db_path = str(tmp_path / "approval_window_review_tables.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    summary = repo.get_approval_window_review_summary()

    assert isinstance(summary, ApprovalWindowReviewSummary)
    assert summary.approval_window_reviews == 0
    assert summary.unique_markets == 0
    assert summary.by_review_status == {}
    assert summary.by_window_state == {}
    assert summary.by_approval_status == {}
    assert summary.latest_reviewed_at is None


def test_approval_window_review_save_list_bundle_summary(tmp_path) -> None:
    db_path = str(tmp_path / "approval_window_review_repo.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    first = make_review(market_id="m1")
    second = make_review(
        market_id="m1",
        review_status=ApprovalWindowReviewStatus.PENDING,
        window_state=ApprovalWindowState.CLOSED,
        recommendation=ApprovalWindowRecommendation.REQUEST_APPROVAL,
    )
    third = make_review(
        market_id="m2",
        review_status=ApprovalWindowReviewStatus.EXPIRED,
        window_state=ApprovalWindowState.EXPIRED,
        recommendation=ApprovalWindowRecommendation.ACKNOWLEDGE_EXPIRY,
    )
    repo.save_approval_window_review_record(first)
    repo.save_approval_window_review_record(second)
    repo.save_approval_window_review_record(third)

    rows = repo.list_approval_window_review_records(limit=10)
    assert len(rows) == 3
    assert rows[0]["approval_window_review_id"] == third.approval_window_review_id
    assert rows[0]["approval_window_valid"] is True

    latest = repo.get_latest_approval_window_review_for_market("m1")
    assert latest is not None
    assert latest["market_id"] == "m1"
    assert latest["window_state"] == "CLOSED"

    bundle = repo.get_approval_window_review_bundle("m1")
    assert isinstance(bundle, ApprovalWindowReviewBundle)
    assert bundle.market_id == "m1"
    assert len(bundle.approval_window_reviews) == 2

    filtered = repo.list_approval_window_review_records(
        market_id="m1",
        review_status=ApprovalWindowReviewStatus.PENDING.value,
    )
    assert len(filtered) == 1
    assert filtered[0]["recommendation"] == "REQUEST_APPROVAL"

    summary = repo.get_approval_window_review_summary()
    assert summary.approval_window_reviews == 3
    assert summary.unique_markets == 2
    assert summary.by_review_status["READY"] == 1
    assert summary.by_review_status["PENDING"] == 1
    assert summary.by_review_status["EXPIRED"] == 1
    assert summary.by_window_state["OPEN"] == 1
    assert summary.by_window_state["CLOSED"] == 1
    assert summary.by_window_state["EXPIRED"] == 1
    assert summary.by_approval_status["PENDING"] == 3
    assert summary.latest_reviewed_at is not None
