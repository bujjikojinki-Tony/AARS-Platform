from __future__ import annotations

from uuid import uuid4

from backend.models.command_review import CommandApprovalStatus
from backend.models.command_review import CommandGateStatus
from backend.models.command_review import CommandReviewBundle
from backend.models.command_review import CommandReviewRecommendation
from backend.models.command_review import CommandReviewRecord
from backend.models.command_review import CommandReviewStatus
from backend.models.command_review import CommandReviewSummary
from backend.storage.db import init_db
from backend.storage.repositories import Repository


def make_review(
    market_id: str = "mock_weather_strong_yes",
    *,
    command_name: str = "/run scan",
    review_status: CommandReviewStatus = CommandReviewStatus.READY,
    approval_status: CommandApprovalStatus = CommandApprovalStatus.PENDING,
    gate_status: CommandGateStatus = CommandGateStatus.BLOCKED,
    recommendation: CommandReviewRecommendation = CommandReviewRecommendation.REVIEW_EVIDENCE,
) -> CommandReviewRecord:
    return CommandReviewRecord(
        command_review_id=f"cr_{uuid4().hex[:10]}",
        market_id=market_id,
        command_name=command_name,
        source_page="command",
        target_page="history",
        command_path="/api/command",
        review_status=review_status,
        approval_status=approval_status,
        recommendation=recommendation,
        gate_status=gate_status,
        active_engine_id="gaussian_v0",
        execution_mode="OBSERVE_ONLY",
        risk_status="SAFE",
        approval_window_valid=True,
        approval_valid_until="2026-06-01T00:00:00+00:00",
        market_snapshot_archive_id="msa_001",
        weather_view_archive_id="wva_001",
        weather_forecast_archive_id="wfa_001",
        probability_run_id="pr_001",
        outcome_resolution_id="or_001",
        calibration_sample_id="cs_001",
        backtest_memory_id="bm_001",
        deb_shadow_run_id="deb_001",
        emos_shadow_run_id="emos_001",
        shadow_evaluation_id="se_001",
        raw_payload={"source": "test"},
        metadata={"case": "command_review"},
    )


def test_command_review_models_serialize():
    review = make_review()
    dumped = review.model_dump(mode="json")
    assert dumped["command_review_id"].startswith("cr_")
    assert dumped["market_id"] == "mock_weather_strong_yes"
    assert dumped["command_name"] == "/run scan"
    assert dumped["review_status"] == "READY"
    assert dumped["approval_status"] == "PENDING"
    assert dumped["gate_status"] == "BLOCKED"
    assert dumped["recommendation"] == "REVIEW_EVIDENCE"
    assert dumped["approval_window_valid"] is True
    assert dumped["metadata"] == {"case": "command_review"}


def test_command_review_tables_created(tmp_path):
    db_path = str(tmp_path / "command_review_tables.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    summary = repo.get_command_review_summary()
    assert isinstance(summary, CommandReviewSummary)
    assert summary.command_reviews == 0
    assert summary.unique_markets == 0
    assert summary.by_review_status == {}
    assert summary.by_approval_status == {}
    assert summary.by_gate_status == {}
    assert summary.latest_reviewed_at is None


def test_command_review_save_list_bundle_summary(tmp_path):
    db_path = str(tmp_path / "command_review_repo.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    first = make_review(market_id="m1")
    second = make_review(
        market_id="m1",
        command_name="/approve_small",
        review_status=CommandReviewStatus.PENDING,
        approval_status=CommandApprovalStatus.APPROVED,
        gate_status=CommandGateStatus.ALLOW,
        recommendation=CommandReviewRecommendation.REQUEST_APPROVAL,
    )
    third = make_review(
        market_id="m2",
        command_name="/block",
        review_status=CommandReviewStatus.BLOCKED,
        approval_status=CommandApprovalStatus.REJECTED,
        gate_status=CommandGateStatus.BLOCKED,
        recommendation=CommandReviewRecommendation.BLOCK,
    )
    repo.save_command_review_record(first)
    repo.save_command_review_record(second)
    repo.save_command_review_record(third)

    rows = repo.list_command_review_records(limit=10)
    assert len(rows) == 3
    assert rows[0]["command_review_id"] == third.command_review_id
    assert rows[0]["approval_window_valid"] is True

    latest = repo.get_latest_command_review_for_market("m1")
    assert latest is not None
    assert latest["command_name"] == "/approve_small"
    assert latest["approval_status"] == "APPROVED"

    bundle = repo.get_command_review_bundle("m1")
    assert isinstance(bundle, CommandReviewBundle)
    assert bundle.market_id == "m1"
    assert len(bundle.command_reviews) == 2

    filtered = repo.list_command_review_records(
        market_id="m1",
        review_status=CommandReviewStatus.PENDING.value,
    )
    assert len(filtered) == 1
    assert filtered[0]["command_name"] == "/approve_small"

    summary = repo.get_command_review_summary()
    assert summary.command_reviews == 3
    assert summary.unique_markets == 2
    assert summary.by_review_status["READY"] == 1
    assert summary.by_review_status["PENDING"] == 1
    assert summary.by_review_status["BLOCKED"] == 1
    assert summary.by_approval_status["PENDING"] == 1
    assert summary.by_approval_status["APPROVED"] == 1
    assert summary.by_approval_status["REJECTED"] == 1
    assert summary.by_gate_status["BLOCKED"] == 2
    assert summary.by_gate_status["ALLOW"] == 1
    assert summary.latest_reviewed_at is not None
