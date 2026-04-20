import json

from typer.testing import CliRunner

from weather_execution_gateway import main as gateway_main
from weather_execution_gateway.polymarket.position_snapshot_producer import (
    PositionSnapshotProducer,
    normalize_balance,
    normalize_open_order,
    normalize_position,
)
from weather_execution_gateway.polymarket.user_activity import PolymarketUserActivityReader


def test_user_activity_reader_loads_local_position_file(tmp_path):
    source_path = tmp_path / "account_positions.json"
    source_path.write_text(
        json.dumps(
            {
                "account_id": "acct_1",
                "positions": [{"market_id": "m1", "size": 10, "current_price": 0.4}],
            }
        ),
        encoding="utf-8",
    )

    payload = PolymarketUserActivityReader(source_path).get_positions()

    assert payload["account_id"] == "acct_1"
    assert payload["positions"][0]["market_id"] == "m1"
    assert payload["source_path"] == str(source_path)


def test_normalize_position_supports_polymarket_aliases():
    normalized = normalize_position(
        {
            "conditionId": "market_1",
            "assetId": "token_1",
            "outcome": "YES",
            "balance": "25",
            "currentPrice": "0.62",
        }
    )

    assert normalized["market_id"] == "market_1"
    assert normalized["token_id"] == "token_1"
    assert normalized["outcome"] == "yes"
    assert normalized["size"] == 25.0
    assert normalized["notional"] == 15.5


def test_normalize_open_order_supports_remaining_size():
    normalized = normalize_open_order(
        {
            "id": "order_1",
            "conditionId": "market_1",
            "assetId": "token_1",
            "side": "YES",
            "status": "OPEN",
            "price": "0.50",
            "size": "20",
            "remainingSize": "8",
        }
    )

    assert normalized["order_id"] == "order_1"
    assert normalized["market_id"] == "market_1"
    assert normalized["token_id"] == "token_1"
    assert normalized["outcome"] == "yes"
    assert normalized["remaining_size"] == 8.0
    assert normalized["notional"] == 4.0


def test_normalize_balance_supports_aliases():
    normalized = normalize_balance(
        {
            "availableBalance": "123.45",
            "totalBalance": "150.00",
            "asset": "USDC",
        }
    )

    assert normalized["available_balance"] == 123.45
    assert normalized["total_balance"] == 150.0
    assert normalized["currency"] == "USDC"
    assert normalized["manual_order_only"] is True
    assert normalized["snapshot_available"] is True


def test_position_snapshot_producer_writes_standard_snapshot(tmp_path):
    source_path = tmp_path / "account_positions.json"
    output_path = tmp_path / "position_snapshot.json"
    source_path.write_text(
        json.dumps(
            {
                "account_id": "acct_1",
                "balance": {
                    "available_balance": 25.0,
                    "total_balance": 50.0,
                    "currency": "USDC",
                    "manual_order_only": True,
                },
                "positions": [
                    {"market_id": "m1", "size": 10, "current_price": 0.4},
                    {"market_id": "m2", "notional": 3.5},
                ],
                "open_orders": [
                    {"order_id": "o1", "market_id": "m1", "price": 0.5, "remaining_size": 8}
                ],
            }
        ),
        encoding="utf-8",
    )

    producer = PositionSnapshotProducer(PolymarketUserActivityReader(source_path))
    producer.write_snapshot(output_path)

    snapshot = json.loads(output_path.read_text(encoding="utf-8"))
    assert snapshot["schema_version"] == "position_snapshot.v1"
    assert snapshot["balance"]["available_balance"] == 25.0
    assert snapshot["balance"]["total_balance"] == 50.0
    assert snapshot["balance"]["manual_order_only"] is True
    assert snapshot["position_count"] == 2
    assert snapshot["open_order_count"] == 1
    assert snapshot["position_notional"] == 7.5
    assert snapshot["open_order_notional"] == 4.0
    assert snapshot["total_notional"] == 11.5
    assert snapshot["positions"][0]["market_id"] == "m1"
    assert snapshot["open_orders"][0]["order_id"] == "o1"


def test_build_position_snapshot_cli_writes_output(monkeypatch, tmp_path):
    source_path = tmp_path / "account_positions.json"
    output_path = tmp_path / "position_snapshot.json"
    source_path.write_text(
        json.dumps(
            {
                "balance": {"available_balance": 9.0, "total_balance": 10.0, "manual_order_only": True},
                "positions": [{"market_id": "m1", "size": 5, "current_price": 0.5}],
                "open_orders": [{"market_id": "m1", "price": 0.5, "remaining_size": 2}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(gateway_main, "POSITION_SOURCE_PATH", source_path)
    monkeypatch.setattr(gateway_main, "POSITION_SNAPSHOT_PATH", output_path)

    result = CliRunner().invoke(gateway_main.app, ["build-position-snapshot"])

    assert result.exit_code == 0
    snapshot = json.loads(output_path.read_text(encoding="utf-8"))
    assert snapshot["position_count"] == 1
    assert snapshot["open_order_count"] == 1
    assert snapshot["balance"]["available_balance"] == 9.0
    assert snapshot["balance"]["manual_order_only"] is True
    assert snapshot["total_notional"] == 3.5
