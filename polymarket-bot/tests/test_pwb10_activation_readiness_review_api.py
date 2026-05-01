from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app_factory import create_app
from backend.models.approval_window_review import ApprovalWindowRecommendation
from backend.models.approval_window_review import ApprovalWindowReviewRecord
from backend.models.approval_window_review import ApprovalWindowReviewStatus
from backend.models.approval_window_review import ApprovalWindowState
from backend.models.core import ExecutionDecision
from backend.models.core import OpportunityCandidate
from backend.models.enums import ActionStatus
from backend.models.enums import ExecutionMode
from backend.models.enums import ExecutionStatus
from backend.models.enums import RiskStatus
from backend.models.enums import Side


def make_client(tmp_path):
    app = create_app(db_path=str(tmp_path / "pwb10_api.sqlite"))
    return TestClient(app)


def seed_execution_context(repo, market_id: str = "m1") -> None:
    candidate = OpportunityCandidate(
        candidate_id=f"cand_{market_id}",
        signal_id=f"sig_{market_id}",
        market_id=market_id,
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
        decision_id=f"dec_{market_id}",
        candidate_id=candidate.candidate_id,
        mode=ExecutionMode.OBSERVE_ONLY,
        action="review",
        position_size=1.0,
        expected_cost=1.0,
        risk_status=RiskStatus.WARN,
        execution_status=ExecutionStatus.QUEUED,
    )
    repo.save_execution_decision(decision)
    approval_review = ApprovalWindowReviewRecord(
        approval_window_review_id=f"awr_{market_id}",
        market_id=market_id,
        decision_id=decision.decision_id,
        candidate_id=candidate.candidate_id,
        approval_status="APPROVED",
        approval_window_valid=True,
        approval_valid_until="2026-06-01T00:00:00Z",
        review_status=ApprovalWindowReviewStatus.READY,
        window_state=ApprovalWindowState.OPEN,
        recommendation=ApprovalWindowRecommendation.REVIEW_WINDOW,
    )
    repo.save_approval_window_review_record(approval_review)


def test_activation_readiness_review_summary_api(tmp_path):
    client = make_client(tmp_path)
    response = client.get("/api/activation-readiness-review/summary")
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "ok"
    assert data["summary"]["activation_readiness_reviews"] == 0


def test_activation_readiness_review_build_and_bundle_api(tmp_path):
    client = make_client(tmp_path)
    repo = client.app.state.repository
    seed_execution_context(repo, "m1")

    response = client.post("/api/activation-readiness-review/build", json={"market_id": "m1"})
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "ok"
    assert data["record"]["market_id"] == "m1"
    assert data["record"]["readiness_status"] == "READY"
    assert data["safety"]["strategy_runner_called"] is False
    assert data["safety"]["execution_triggered"] is False

    summary = client.get("/api/activation-readiness-review/summary").json()
    assert summary["summary"]["activation_readiness_reviews"] == 1
    assert summary["summary"]["unique_markets"] == 1

    reviews = client.get("/api/activation-readiness-review/reviews?limit=10").json()
    assert reviews["status"] == "ok"
    assert len(reviews["items"]) == 1

    bundle = client.get("/api/activation-readiness-review/market/m1").json()
    assert bundle["status"] == "ok"
    assert bundle["market_id"] == "m1"
    assert len(bundle["bundle"]["activation_readiness_reviews"]) == 1


def test_activation_readiness_review_build_all_api(tmp_path):
    client = make_client(tmp_path)
    repo = client.app.state.repository
    seed_execution_context(repo, "m1")
    seed_execution_context(repo, "m2")

    response = client.post("/api/activation-readiness-review/build-all", json={})
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "ok"
    assert data["built_count"] == 2
    assert data["safety"]["probability_engine_called"] is False
    assert data["safety"]["active_engine_changed"] is False
