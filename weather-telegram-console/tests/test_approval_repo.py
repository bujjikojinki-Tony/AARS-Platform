from weather_telegram_console.storage.session_repo import ApprovalRepository
from weather_telegram_console.storage.sqlite import SQLiteStore


def test_create_and_find_active_approval(tmp_path):
    db_path = tmp_path / "test.db"
    store = SQLiteStore(str(db_path))
    repo = ApprovalRepository(store)

    approval = repo.create_approval(
        signal_id="sig_001",
        operator_user_id=123,
        decision="approve_small",
        ttl_minutes=15,
        intent_id="intent_001",
    )

    found = repo.find_active_approval("sig_001")

    assert found is not None
    assert found["approval_id"] == approval["approval_id"]
    assert found["intent_id"] == "intent_001"


def test_get_signal_approval_status(tmp_path):
    db_path = tmp_path / "test.db"
    store = SQLiteStore(str(db_path))
    repo = ApprovalRepository(store)

    repo.create_approval(
        signal_id="sig_active",
        operator_user_id=123,
        decision="approve_small",
        ttl_minutes=15,
        intent_id="intent_active",
    )
    repo.create_approval(
        signal_id="sig_expired",
        operator_user_id=123,
        decision="approve_small",
        ttl_minutes=-1,
        intent_id="intent_expired",
    )
    consumed = repo.create_approval(
        signal_id="sig_consumed",
        operator_user_id=123,
        decision="approve_small",
        ttl_minutes=15,
        intent_id="intent_consumed",
    )
    repo.mark_consumed(consumed["approval_id"])

    assert repo.get_signal_approval_status("sig_active")["status"] == "已审批"
    assert repo.get_signal_approval_status("sig_expired")["status"] == "已过期"
    assert repo.get_signal_approval_status("sig_consumed")["status"] == "已消费"
    assert repo.get_signal_approval_status("sig_missing")["status"] == "未审批"
