from __future__ import annotations

from uuid import uuid4

from backend.models.activation_readiness_review import ActivationReadinessRecommendation
from backend.models.activation_readiness_review import ActivationReadinessReviewBundle
from backend.models.activation_readiness_review import ActivationReadinessReviewRecord
from backend.models.activation_readiness_review import ActivationReadinessReviewStatus
from backend.models.activation_readiness_review import ActivationReadinessReviewSummary
from backend.storage.db import init_db
from backend.storage.repositories import Repository


def make_review(
    market_id: str = "mock_weather_strong_yes",
    *,
    readiness_status: ActivationReadinessReviewStatus = ActivationReadinessReviewStatus.READY,
    recommendation: ActivationReadinessRecommendation = ActivationReadinessRecommendation.READY_FOR_GOVERNED_REVIEW,
) -> ActivationReadinessReviewRecord:
    return ActivationReadinessReviewRecord(
        activation_readiness_review_id=f"arr_{uuid4().hex[:10]}",
        market_id=market_id,
        decision_id=f"dec_{uuid4().hex[:10]}",
        candidate_id=f"cand_{uuid4().hex[:10]}",
        command_review_id="crv_001",
        execution_decision_review_id="edr_001",
        execution_queue_review_id="eqr_001",
        approval_window_review_id="awr_001",
        approval_status="PENDING",
        window_state="OPEN",
        review_status="READY",
        readiness_status=readiness_status,
        recommendation=recommendation,
        raw_payload={"source": "test"},
        metadata={"case": "activation_readiness_review"},
    )


def test_activation_readiness_review_models_serialize() -> None:
    review = make_review()
    dumped = review.model_dump(mode="json")

    assert dumped["activation_readiness_review_id"].startswith("arr_")
    assert dumped["market_id"] == "mock_weather_strong_yes"
    assert dumped["readiness_status"] == "READY"
    assert dumped["recommendation"] == "READY_FOR_GOVERNED_REVIEW"
    assert dumped["window_state"] == "OPEN"


def test_activation_readiness_review_tables_created(tmp_path) -> None:
    db_path = str(tmp_path / "activation_readiness_review_tables.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    summary = repo.get_activation_readiness_review_summary()

    assert isinstance(summary, ActivationReadinessReviewSummary)
    assert summary.activation_readiness_reviews == 0
    assert summary.unique_markets == 0
    assert summary.by_readiness_status == {}
    assert summary.by_recommendation == {}
    assert summary.by_approval_status == {}
    assert summary.latest_reviewed_at is None


def test_activation_readiness_review_save_list_bundle_summary(tmp_path) -> None:
    db_path = str(tmp_path / "activation_readiness_review_repo.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    first = make_review(market_id="m1")
    second = make_review(
        market_id="m1",
        readiness_status=ActivationReadinessReviewStatus.NEEDS_REVIEW,
        recommendation=ActivationReadinessRecommendation.REVIEW_GOVERNANCE,
    )
    third = make_review(
        market_id="m2",
        readiness_status=ActivationReadinessReviewStatus.NOT_READY,
        recommendation=ActivationReadinessRecommendation.HOLD_OBSERVE_ONLY,
    )
    repo.save_activation_readiness_review_record(first)
    repo.save_activation_readiness_review_record(second)
    repo.save_activation_readiness_review_record(third)

    rows = repo.list_activation_readiness_review_records(limit=10)
    assert len(rows) == 3
    assert rows[0]["activation_readiness_review_id"] == third.activation_readiness_review_id
    assert rows[0]["approval_status"] == "PENDING"

    latest = repo.get_latest_activation_readiness_review_for_market("m1")
    assert latest is not None
    assert latest["market_id"] == "m1"
    assert latest["readiness_status"] == "NEEDS_REVIEW"

    bundle = repo.get_activation_readiness_review_bundle("m1")
    assert isinstance(bundle, ActivationReadinessReviewBundle)
    assert bundle.market_id == "m1"
    assert len(bundle.activation_readiness_reviews) == 2

    filtered = repo.list_activation_readiness_review_records(
        market_id="m1",
        readiness_status=ActivationReadinessReviewStatus.NEEDS_REVIEW.value,
    )
    assert len(filtered) == 1
    assert filtered[0]["recommendation"] == "REVIEW_GOVERNANCE"

    summary = repo.get_activation_readiness_review_summary()
    assert summary.activation_readiness_reviews == 3
    assert summary.unique_markets == 2
    assert summary.by_readiness_status["READY"] == 1
    assert summary.by_readiness_status["NEEDS_REVIEW"] == 1
    assert summary.by_readiness_status["NOT_READY"] == 1
    assert summary.by_recommendation["READY_FOR_GOVERNED_REVIEW"] == 1
    assert summary.by_recommendation["REVIEW_GOVERNANCE"] == 1
    assert summary.by_recommendation["HOLD_OBSERVE_ONLY"] == 1
    assert summary.by_approval_status["PENDING"] == 3
    assert summary.latest_reviewed_at is not None
