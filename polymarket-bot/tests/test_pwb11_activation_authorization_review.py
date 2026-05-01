from __future__ import annotations

from uuid import uuid4

from backend.models.activation_authorization_review import ActivationAuthorizationRecommendation
from backend.models.activation_authorization_review import ActivationAuthorizationReviewBundle
from backend.models.activation_authorization_review import ActivationAuthorizationReviewRecord
from backend.models.activation_authorization_review import ActivationAuthorizationReviewStatus
from backend.models.activation_authorization_review import ActivationAuthorizationReviewSummary
from backend.storage.db import init_db
from backend.storage.repositories import Repository


def make_review(
    market_id: str = "mock_weather_strong_yes",
    *,
    authorization_status: ActivationAuthorizationReviewStatus = ActivationAuthorizationReviewStatus.AUTHORIZED,
    recommendation: ActivationAuthorizationRecommendation = ActivationAuthorizationRecommendation.READY_FOR_AUTHORIZATION_REVIEW,
) -> ActivationAuthorizationReviewRecord:
    return ActivationAuthorizationReviewRecord(
        activation_authorization_review_id=f"aar_{uuid4().hex[:10]}",
        market_id=market_id,
        decision_id=f"dec_{uuid4().hex[:10]}",
        candidate_id=f"cand_{uuid4().hex[:10]}",
        command_review_id="crv_001",
        execution_decision_review_id="edr_001",
        execution_queue_review_id="eqr_001",
        approval_window_review_id="awr_001",
        activation_readiness_review_id="arr_001",
        approval_status="APPROVED",
        window_state="OPEN",
        readiness_status="READY",
        authorization_status=authorization_status,
        recommendation=recommendation,
        raw_payload={"source": "test"},
        metadata={"case": "activation_authorization_review"},
    )


def test_activation_authorization_review_models_serialize() -> None:
    review = make_review()
    dumped = review.model_dump(mode="json")

    assert dumped["activation_authorization_review_id"].startswith("aar_")
    assert dumped["market_id"] == "mock_weather_strong_yes"
    assert dumped["authorization_status"] == "AUTHORIZED"
    assert dumped["recommendation"] == "READY_FOR_AUTHORIZATION_REVIEW"
    assert dumped["readiness_status"] == "READY"


def test_activation_authorization_review_tables_created(tmp_path) -> None:
    db_path = str(tmp_path / "activation_authorization_review_tables.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    summary = repo.get_activation_authorization_review_summary()

    assert isinstance(summary, ActivationAuthorizationReviewSummary)
    assert summary.activation_authorization_reviews == 0
    assert summary.unique_markets == 0
    assert summary.by_authorization_status == {}
    assert summary.by_recommendation == {}
    assert summary.by_approval_status == {}
    assert summary.latest_reviewed_at is None


def test_activation_authorization_review_save_list_bundle_summary(tmp_path) -> None:
    db_path = str(tmp_path / "activation_authorization_review_repo.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    first = make_review(market_id="m1")
    second = make_review(
        market_id="m1",
        authorization_status=ActivationAuthorizationReviewStatus.NEEDS_AUTHORIZATION,
        recommendation=ActivationAuthorizationRecommendation.REQUEST_AUTHORIZATION,
    )
    third = make_review(
        market_id="m2",
        authorization_status=ActivationAuthorizationReviewStatus.NOT_AUTHORIZED,
        recommendation=ActivationAuthorizationRecommendation.HOLD_OBSERVE_ONLY,
    )
    repo.save_activation_authorization_review_record(first)
    repo.save_activation_authorization_review_record(second)
    repo.save_activation_authorization_review_record(third)

    rows = repo.list_activation_authorization_review_records(limit=10)
    assert len(rows) == 3
    assert rows[0]["activation_authorization_review_id"] == third.activation_authorization_review_id
    assert rows[0]["approval_status"] == "APPROVED"

    latest = repo.get_latest_activation_authorization_review_for_market("m1")
    assert latest is not None
    assert latest["market_id"] == "m1"
    assert latest["authorization_status"] == "NEEDS_AUTHORIZATION"

    bundle = repo.get_activation_authorization_review_bundle("m1")
    assert isinstance(bundle, ActivationAuthorizationReviewBundle)
    assert bundle.market_id == "m1"
    assert len(bundle.activation_authorization_reviews) == 2

    filtered = repo.list_activation_authorization_review_records(
        market_id="m1",
        authorization_status=ActivationAuthorizationReviewStatus.NEEDS_AUTHORIZATION.value,
    )
    assert len(filtered) == 1
    assert filtered[0]["recommendation"] == "REQUEST_AUTHORIZATION"

    summary = repo.get_activation_authorization_review_summary()
    assert summary.activation_authorization_reviews == 3
    assert summary.unique_markets == 2
    assert summary.by_authorization_status["AUTHORIZED"] == 1
    assert summary.by_authorization_status["NEEDS_AUTHORIZATION"] == 1
    assert summary.by_authorization_status["NOT_AUTHORIZED"] == 1
    assert summary.by_recommendation["READY_FOR_AUTHORIZATION_REVIEW"] == 1
    assert summary.by_recommendation["REQUEST_AUTHORIZATION"] == 1
    assert summary.by_recommendation["HOLD_OBSERVE_ONLY"] == 1
    assert summary.by_approval_status["APPROVED"] == 3
    assert summary.latest_reviewed_at is not None
