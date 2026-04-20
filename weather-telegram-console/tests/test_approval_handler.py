import asyncio
import json

from weather_telegram_console.bot.handlers.approvals import approval_callback_handler
from weather_telegram_console.integrations.intent_writer import IntentWriter
from weather_telegram_console.storage.sqlite import SQLiteStore


class FakeUser:
    def __init__(self, user_id: int, username: str | None = None) -> None:
        self.id = user_id
        self.username = username


class FakeQuery:
    def __init__(self, data: str, user_id: int = 123, username: str | None = None) -> None:
        self.data = data
        self.edited_text: str | None = None
        self.parse_mode: str | None = None
        self.answered = False
        self.from_user = FakeUser(user_id=user_id, username=username)

    async def answer(self) -> None:
        self.answered = True

    async def edit_message_text(self, text: str, parse_mode: str | None = None) -> None:
        self.edited_text = text
        self.parse_mode = parse_mode


class FakeUpdate:
    def __init__(self, data: str, user_id: int = 123, username: str | None = None) -> None:
        self.callback_query = FakeQuery(data=data, user_id=user_id, username=username)


def test_approval_handler_watch_action(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_ADMIN_USER_IDS", "123")
    update = FakeUpdate("watch:sig_1", user_id=123)
    asyncio.run(approval_callback_handler(update, None))
    assert update.callback_query.answered is True
    assert update.callback_query.edited_text == "Signal `sig_1` marked as WATCH."


def test_approval_handler_approve_action(monkeypatch, tmp_path) -> None:
    signal_path = tmp_path / "test_signal_event.json"
    pending_dir = tmp_path / "pending_intents"
    db_path = tmp_path / "weather_telegram_console.db"
    audit_path = tmp_path / "manual_advisory_audit.jsonl"
    monkeypatch.setenv("SIGNAL_JSON_PATH", str(signal_path))
    monkeypatch.setenv("MANUAL_ADVISORY_AUDIT_JSONL", str(audit_path))
    with open(signal_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "signal_id": "sig_1",
                "market_id": "sample_market_001",
                "execution_mode": "manual_advisory",
                "manual_order_required": True,
                "autonomous_execution_allowed": False,
                "manual_trade_ticket": {
                    "market_id": "sample_market_001",
                    "recommended_side": "buy",
                    "limit_price": 0.61,
                    "size": 10.0,
                },
                "edge_direction": "divergent",
                "model_value": 28.1,
            },
            f,
        )

    monkeypatch.setattr(
        "weather_telegram_console.bot.handlers.approvals.SQLiteStore",
        lambda: SQLiteStore(db_path=str(db_path)),
    )
    monkeypatch.setattr(
        "weather_telegram_console.bot.handlers.approvals.IntentWriter",
        lambda: IntentWriter(output_dir=str(pending_dir)),
    )
    update = FakeUpdate("approve:sig_1", user_id=123)
    asyncio.run(approval_callback_handler(update, None))
    assert "Signal `sig_1` marked as APPROVE SMALL." in update.callback_query.edited_text
    assert "Approval ID:" in update.callback_query.edited_text
    assert "Expires At:" in update.callback_query.edited_text
    assert "Saved to:" in update.callback_query.edited_text
    intent_files = list(pending_dir.glob("*.json"))
    assert len(intent_files) == 1
    with open(intent_files[0], "r", encoding="utf-8") as f:
        payload = json.load(f)
    assert payload["market_id"] == "sample_market_001"
    assert payload["signal_id"] == "sig_1"
    assert payload["approved"] is True

    store = SQLiteStore(str(db_path))
    cur = store.conn.cursor()
    cur.execute("SELECT intent_id FROM approvals LIMIT 1")
    row = cur.fetchone()
    assert row is not None
    assert row[0] == payload["intent_id"]
    audit_text = audit_path.read_text(encoding="utf-8")
    assert "operator_acknowledged_manual_advisory" in audit_text
    assert "operator_review_not_auto_execution" in audit_text


def test_approval_handler_reuses_existing_dashboard_intent(monkeypatch, tmp_path) -> None:
    signal_path = tmp_path / "test_signal_event.json"
    pending_dir = tmp_path / "pending_intents"
    db_path = tmp_path / "weather_telegram_console.db"
    dashboard_preview = tmp_path / "dashboard_intent_preview.json"
    monkeypatch.setenv("SIGNAL_JSON_PATH", str(signal_path))
    monkeypatch.setenv("DASHBOARD_INTENT_PREVIEW_PATH", str(dashboard_preview))

    with open(signal_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "signal_id": "sig_1",
                "market_id": "sample_market_001",
                "edge_direction": "divergent",
                "model_value": 28.1,
            },
            f,
        )

    with open(dashboard_preview, "w", encoding="utf-8") as f:
        json.dump(
            {
                "intent_id": "intent_dashboard_123",
                "market_id": "sample_market_001",
                "signal_id": "dashboard_sample_market_001_123",
                "side": "buy",
                "price": 0.61,
                "size": 10.0,
                "post_only": True,
                "max_slippage_pct": 0.02,
                "approved": True,
            },
            f,
        )

    monkeypatch.setattr(
        "weather_telegram_console.bot.handlers.approvals.SQLiteStore",
        lambda: SQLiteStore(db_path=str(db_path)),
    )
    monkeypatch.setattr(
        "weather_telegram_console.bot.handlers.approvals.IntentWriter",
        lambda: IntentWriter(output_dir=str(pending_dir)),
    )

    update = FakeUpdate("approve:sig_1", user_id=123)
    asyncio.run(approval_callback_handler(update, None))

    assert "Intent ID: `intent_dashboard_123`" in update.callback_query.edited_text
    assert "existing_dashboard_or_pending_intent" in update.callback_query.edited_text
    intent_files = list(pending_dir.glob("*.json"))
    assert len(intent_files) == 1
    payload = json.loads(intent_files[0].read_text(encoding="utf-8"))
    assert payload["intent_id"] == "intent_dashboard_123"
    assert payload["schema_version"] == "execution_intent.v1"
    assert payload["authorization_ref"].startswith("approval_")
    assert payload["decision_ref"].startswith("decision_telegram_")


def test_approval_handler_reuses_active_approval(monkeypatch, tmp_path) -> None:
    signal_path = tmp_path / "test_signal_event.json"
    pending_dir = tmp_path / "pending_intents"
    db_path = tmp_path / "weather_telegram_console.db"
    monkeypatch.setenv("SIGNAL_JSON_PATH", str(signal_path))
    with open(signal_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "signal_id": "sig_1",
                "market_id": "sample_market_001",
                "edge_direction": "divergent",
                "model_value": 28.1,
            },
            f,
        )

    monkeypatch.setattr(
        "weather_telegram_console.bot.handlers.approvals.SQLiteStore",
        lambda: SQLiteStore(db_path=str(db_path)),
    )
    monkeypatch.setattr(
        "weather_telegram_console.bot.handlers.approvals.IntentWriter",
        lambda: IntentWriter(output_dir=str(pending_dir)),
    )

    update_1 = FakeUpdate("approve:sig_1", user_id=123)
    asyncio.run(approval_callback_handler(update_1, None))
    first_files = list(pending_dir.glob("*.json"))
    assert len(first_files) == 1

    update_2 = FakeUpdate("approve:sig_1", user_id=123)
    asyncio.run(approval_callback_handler(update_2, None))
    assert "already has an active approval" in update_2.callback_query.edited_text
    assert len(list(pending_dir.glob("*.json"))) == 1
