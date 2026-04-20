import json

from typer.testing import CliRunner

from weather_execution_gateway import main as gateway_main
from weather_execution_gateway.advisory.fill_reconciliation import HumanFillReconciler


def test_human_fill_reconciler_marks_matching_position_as_reconciled(tmp_path):
    fills_path = tmp_path / "human_fills.jsonl"
    position_path = tmp_path / "position_snapshot.json"
    intent_path = tmp_path / "dashboard_intent_preview.json"
    fills_path.write_text(
        json.dumps(
            {
                "fill_id": "fill_1",
                "intent_id": "intent_1",
                "signal_id": "sig_1",
                "market_id": "market_1",
                "side": "buy",
                "price": 0.61,
                "size": 10,
                "notional": 6.1,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    position_path.write_text(
        json.dumps(
            {
                "updated_at": "2026-04-18T00:00:00+00:00",
                "positions": [
                    {
                        "market_id": "market_1",
                        "outcome": "yes",
                        "current_price": 0.61,
                        "size": 10,
                        "notional": 6.1,
                    }
                ],
                "open_orders": [],
            }
        ),
        encoding="utf-8",
    )
    intent_path.write_text(
        json.dumps({"intent_id": "intent_1", "price": 0.61}),
        encoding="utf-8",
    )

    report = HumanFillReconciler(
        fills_path=fills_path,
        position_snapshot_path=position_path,
        intent_preview_path=intent_path,
    ).build_report()

    assert report["overall_status"] == "reconciled"
    assert report["reconciled_count"] == 1
    assert report["items"][0]["reconciliation_status"] == "reconciled"
    assert report["items"][0]["checks"]["position_or_order_covers_fill"] is True
    assert report["items"][0]["checks"]["price_within_tolerance"] is True


def test_human_fill_reconciler_marks_missing_position_as_unmatched(tmp_path):
    fills_path = tmp_path / "human_fills.jsonl"
    position_path = tmp_path / "position_snapshot.json"
    fills_path.write_text(
        json.dumps(
            {
                "fill_id": "fill_1",
                "intent_id": "intent_1",
                "market_id": "market_1",
                "side": "buy",
                "price": 0.61,
                "size": 10,
                "notional": 6.1,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    position_path.write_text(
        json.dumps({"positions": [], "open_orders": []}),
        encoding="utf-8",
    )

    report = HumanFillReconciler(
        fills_path=fills_path,
        position_snapshot_path=position_path,
    ).build_report()

    assert report["overall_status"] == "needs_review"
    assert report["unmatched_count"] == 1
    assert report["items"][0]["review_reason"] == "fill_market_not_seen_in_position_snapshot"


def test_reconcile_human_fills_cli_writes_report(monkeypatch, tmp_path):
    fills_path = tmp_path / "fills.jsonl"
    position_path = tmp_path / "position_snapshot.json"
    report_path = tmp_path / "reconciliation_report.json"
    intent_path = tmp_path / "dashboard_intent_preview.json"
    fills_path.write_text(
        json.dumps(
            {
                "fill_id": "fill_1",
                "intent_id": "intent_1",
                "market_id": "market_1",
                "side": "buy",
                "price": 0.61,
                "size": 10,
                "notional": 6.1,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    position_path.write_text(
        json.dumps({"positions": [{"market_id": "market_1", "notional": 6.1}], "open_orders": []}),
        encoding="utf-8",
    )
    intent_path.write_text(json.dumps({"intent_id": "intent_1", "price": 0.61}), encoding="utf-8")
    monkeypatch.setattr(gateway_main, "HUMAN_FILLS_PATH", fills_path)
    monkeypatch.setattr(gateway_main, "POSITION_SNAPSHOT_PATH", position_path)
    monkeypatch.setattr(gateway_main, "HUMAN_FILL_RECONCILIATION_REPORT_PATH", report_path)
    monkeypatch.setattr(gateway_main, "DASHBOARD_INTENT_PREVIEW_PATH", intent_path)

    result = CliRunner().invoke(gateway_main.app, ["reconcile-human-fills"])

    assert result.exit_code == 0
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["overall_status"] == "reconciled"
    assert "Human fill reconciliation report written" in result.output
