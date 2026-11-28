# OMB-003 回退至 OMB-002-FIX 隔离演练

TM-RELEASE-05 本轮结果为 `PASS_ISOLATED_REHEARSAL`。在 MacBook 上通过真实 MCP stdio 依次运行 003、002 和 003。

1. 在独立 003 库创建一条合成草稿，读取创建事件，正常停止协调器。
2. 将 002 启动器复制到临时目录，仅替换数据库路径。使用冻结库的 SQLite 一致性副本启动，健康结果为 `HEALTHY`，两条历史合成任务各读回 9 个通过存储层完整性验证的对象。
3. 002 运行阶段，隔离 003 库的 SHA-256 保持一致。再次启动 003 后读回相同草稿与事件。演练前后四项冻结输入的登记 SHA-256 全部匹配。

复现时，在 003E 工作树设置 `PYTHONPATH=src:frozen_payload/source/src`，以 `.venv/bin/python scripts/check_003e_rollback.py` 执行。脚本退出码为 0。

本轮覆盖进程与存储回滚。OpenMausBot 实际配置切换仍待正式验收。正式签名、公钥激活及本人在场审批继续受阻，003F 和 003G 保持 `HOLD`，总裁决保持 `BLOCKED`。

## 复现脚本

```python
"""Rehearse 003 shutdown, 002 service recovery and 003 readback on isolated databases."""
import json
from pathlib import Path
from shlex import quote
import sqlite3
import sys
import tempfile
from contextlib import closing, contextmanager
from uuid import uuid4

from check_003e_mcp import ROOT, RawSession, file_hash, registered_frozen_hashes


@contextmanager
def mcp_process(command, version):
    session = RawSession(command)
    try:
        _, response = session.request("initialize", {
            "protocolVersion": version, "capabilities": {},
            "clientInfo": {"name": "omb-rollback-rehearsal", "version": "1"},
        }, 1)
        assert response["result"]["protocolVersion"] == version
        session.notify("notifications/initialized")
        yield session
        session.proc.stdin.close()
        assert session.proc.wait(timeout=8) == 0
        assert session.proc.stdout.read() == session.proc.stderr.read() == b""
    finally:
        if session.proc.poll() is None:
            session.proc.kill()
            session.proc.wait(timeout=3)
        session.selector.close()
        for pipe in (session.proc.stdin, session.proc.stdout, session.proc.stderr):
            pipe.close()


def call(session, request_id, tool, arguments):
    _, response = session.request("tools/call", {"name": tool, "arguments": arguments}, request_id)
    result = response["result"]
    assert not result["isError"]
    return json.loads(result["content"][0]["text"])


def verify_frozen():
    registered = registered_frozen_hashes()
    assert all(file_hash(path) == expected for path, expected in registered.items())
    return len(registered)


def run():
    confirmed = verify_frozen()
    config = json.loads((ROOT / "frozen_payload/RUNTIME_BINDING.json").read_text())
    source_db = Path(config["database_path"])
    original_launcher = Path(config["launcher_path"]).read_text()
    expected_assignment = f"export AARS_OMB_DB={source_db}\n"
    assert original_launcher.count(expected_assignment) == 1
    base = ROOT / ".devdata"
    base.mkdir(mode=0o700, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="rollback-", dir=base) as temporary:
        directory = Path(temporary)
        legacy_db = directory / "legacy.sqlite"
        with closing(sqlite3.connect(source_db.as_uri() + "?mode=ro", uri=True)) as source:
            with closing(sqlite3.connect(legacy_db)) as copy:
                source.backup(copy)
        launcher = directory / "launch-aars-mcp"
        launcher.write_text(original_launcher.replace(
            expected_assignment, f"export AARS_OMB_DB={quote(str(legacy_db))}\n"))
        launcher.chmod(0o700)
        development = directory / "development"
        development.mkdir(mode=0o700)
        command = [sys.executable, "-m", "aars_task_manager.mcp_server",
                   "--supervise", "--data-root", str(development)]
        with mcp_process(command, "2025-11-25") as session:
            created = call(session, 2, "aars_task_create_v1", {
                "title": "Isolated rollback draft", "description": "",
                "purpose": "LOCAL_SYNTHETIC_VALIDATION", "idempotency_key": str(uuid4()),
            })
            assert created["ok"] and created["execution_authorized"] is False
            task = created["data"]["task"]
            assert task["state"] == "DRAFT"
            task_args = {"task_id": task["task_id"]}
            initial_events = call(session, 3, "aars_task_events_v1", task_args)["data"]
            assert len(initial_events["events"]) == 1
        inactive_hash = file_hash(development / "tasks.sqlite")

        with mcp_process([str(launcher)], "2024-11-05") as session:
            health = call(session, 2, "aars_health", {})
            assert health["status"] == "HEALTHY"
            object_counts = []
            for request_id, task_id in enumerate(("OMB-SIM-MacBook-FIX", "OMB-SIM-BotAcceptance"), start=3):
                result = call(session, request_id, "aars_task_objects", {"task_id": task_id})
                assert result["found"] and result["object_count"] == len(result["objects"]) == 9
                object_counts.append(result["object_count"])
        assert file_hash(development / "tasks.sqlite") == inactive_hash

        with mcp_process(command, "2025-11-25") as session:
            restored = call(session, 2, "aars_task_get_v1", task_args)
            assert restored["ok"] and restored["execution_authorized"] is False
            assert restored["data"]["task"] == task
            assert call(session, 3, "aars_task_events_v1", task_args)["data"] == initial_events
    assert verify_frozen() == confirmed
    return {
        "status": "PASS_ISOLATED_REHEARSAL",
        "legacy_health": health["status"],
        "legacy_verified_object_counts": object_counts,
        "development_database_unchanged_during_legacy_service": True,
        "development_draft_and_events_restored": True,
        "frozen_inputs_verified": confirmed,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
```
