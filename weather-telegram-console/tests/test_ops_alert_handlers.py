import asyncio
import json

from weather_telegram_console.bot.handlers.ops_alerts import opsack_handler, opsqueue_handler


class FakeSentMessage:
    def __init__(self, message_id: int) -> None:
        self.message_id = message_id


class FakeMessage:
    def __init__(self) -> None:
        self.replies: list[str] = []
        self._counter = 100

    async def reply_text(self, text: str, parse_mode: str | None = None):
        self.replies.append(text)
        self._counter += 1
        return FakeSentMessage(self._counter)


class FakeUser:
    def __init__(self, user_id: int, username: str | None = None) -> None:
        self.id = user_id
        self.username = username


class FakeChat:
    def __init__(self, chat_id: int = 999) -> None:
        self.id = chat_id


class FakeUpdate:
    def __init__(self, user_id: int = 123, username: str | None = "admin") -> None:
        self.message = FakeMessage()
        self.effective_user = FakeUser(user_id, username)
        self.effective_chat = FakeChat()


class FakeContext:
    def __init__(self, args: list[str] | None = None) -> None:
        self.args = args or []


def test_opsqueue_handler_dispatches_pending(monkeypatch, tmp_path) -> None:
    queue_path = tmp_path / "telegram_ops_notifications.jsonl"
    delivery_log = tmp_path / "telegram_ops_delivery_log.jsonl"
    queue_path.write_text(
        json.dumps(
            {
                "schema_version": "telegram_ops_notification.v1",
                "notification_id": "ops_99",
                "status": "pending",
                "channel": "telegram_ops_bridge",
                "text": "ops alert text",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("TELEGRAM_ADMIN_USER_IDS", "123")
    monkeypatch.setenv("TELEGRAM_OPS_NOTIFICATIONS_JSONL", str(queue_path))
    monkeypatch.setenv("TELEGRAM_OPS_DELIVERY_LOG_JSONL", str(delivery_log))

    update = FakeUpdate(user_id=123, username="admin")
    context = FakeContext(["5"])
    asyncio.run(opsqueue_handler(update, context))

    assert any("ops alert text" in msg for msg in update.message.replies)
    assert any("Ops queue dispatched: 1 sent." in msg for msg in update.message.replies)
    payload = json.loads(queue_path.read_text(encoding="utf-8").strip())
    assert payload["status"] == "sent"
    assert payload["sent_by"] == "telegram_bot"
    assert payload["sent_channel"] == "telegram_bot"
    assert delivery_log.exists()


def test_opsqueue_handler_denies_non_admin(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("TELEGRAM_ADMIN_USER_IDS", "123")
    monkeypatch.setenv("TELEGRAM_OPS_NOTIFICATIONS_JSONL", str(tmp_path / "queue.jsonl"))
    monkeypatch.setenv("TELEGRAM_OPS_DELIVERY_LOG_JSONL", str(tmp_path / "delivery.jsonl"))

    update = FakeUpdate(user_id=456, username="guest")
    asyncio.run(opsqueue_handler(update, FakeContext()))

    assert update.message.replies[-1] == "Access denied: admin only."


def test_opsack_handler_acks_notification(monkeypatch, tmp_path) -> None:
    queue_path = tmp_path / "telegram_ops_notifications.jsonl"
    delivery_log = tmp_path / "telegram_ops_delivery_log.jsonl"
    queue_path.write_text(
        json.dumps(
            {
                "schema_version": "telegram_ops_notification.v1",
                "notification_id": "ops_acked",
                "status": "sent",
                "channel": "telegram_ops_bridge",
                "text": "ops alert text",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("TELEGRAM_ADMIN_USER_IDS", "123")
    monkeypatch.setenv("TELEGRAM_OPS_NOTIFICATIONS_JSONL", str(queue_path))
    monkeypatch.setenv("TELEGRAM_OPS_DELIVERY_LOG_JSONL", str(delivery_log))

    update = FakeUpdate(user_id=123, username="ops_admin")
    context = FakeContext(["ops_acked"])
    asyncio.run(opsack_handler(update, context))

    assert update.message.replies[-1] == "Acked ops notification: ops_acked"
    payload = json.loads(queue_path.read_text(encoding="utf-8").strip())
    assert payload["status"] == "acked"
    assert payload["acked_by"] == "ops_admin"
    assert delivery_log.exists()
