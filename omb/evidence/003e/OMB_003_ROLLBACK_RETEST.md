# OMB-003 迁移回滚补验

裁决仍为 `BLOCKED`。本机有效代码签名身份为零，操作者确认继续暂缓签名设置。003D 的正式签名双向 XPC、可信公钥激活及本人在场审批待验。003F 与 003G 保持 `HOLD`。

在隔离 D4 合成库上运行当前 D5 迁移实现。测试在临时库完成校验、正式目标文件发布之前注入 I/O 错误。迁移报告失败，目标目录清理完毕。原 D4 库字节一致，以只读方式重开后完整性检查通过。解除故障后迁移重试成功，D5 中的任务、证据及审批历史与原库一致。

聚焦回归 41/41 通过。全量回归 329/329 通过，其中 32 项为 OMB-002-FIX 历史测试。复核四项冻结输入，SHA-256 均匹配。复现入口为 `tests/test_d4_migration.py` 中的 `test_copy_publish_io_failure_leaves_original_readable_and_retryable`。

TM-RELEASE-03 增加本机模拟发布 I/O 故障通过的证据。该用例覆盖错误返回、原库保留和重试，正式部署候选的迁移演练仍待验收。TM-MCP-08 的 HTML 执行隔离和 Evidence 界面渲染仍待补证。

## 本轮测试补丁

```diff
diff --git a/tests/test_d4_migration.py b/tests/test_d4_migration.py
index c8e516e..f606aa0 100644
--- a/tests/test_d4_migration.py
+++ b/tests/test_d4_migration.py
@@ -1,8 +1,11 @@
+import errno
 import fcntl
 import sqlite3
+from contextlib import closing
 
 import pytest
 
+from aars_task_manager import migration
 from aars_task_manager.approval_enrollment import EnrollmentAnchor
 from aars_task_manager.approval_transactions import ResultDecisionStore
 from aars_task_manager.domain import new_id
@@ -136,3 +139,34 @@ def test_copy_clears_a_valid_stale_boot_marker(system, tmp_path):
     new = target_copy(repo, target, system['protected'])
     assert new.read(lambda db: new.meta(db, 'active_boot')) == ''
     assert repo.path.read_bytes() == before
+
+
+def test_copy_publish_io_failure_leaves_original_readable_and_retryable(system, tmp_path, monkeypatch):
+    repo, _, _, _, _ = offline_d4(system, revoked=True)
+    source_bytes = repo.path.read_bytes()
+    target = tmp_path / 'publish-failure'
+    target.mkdir(mode=0o700)
+
+    def fail_publish(source, destination):
+        assert source.is_file() and destination == target / 'tasks.sqlite'
+        raise OSError(errno.EIO, 'simulated error publishing completed migration')
+
+    with monkeypatch.context() as patches:
+        patches.setattr(migration.os, 'link', fail_publish)
+        with pytest.raises(OSError) as failure:
+            target_copy(repo, target, system['protected'])
+        assert failure.value.errno == errno.EIO
+
+    assert list(target.iterdir()) == []
+    assert repo.path.read_bytes() == source_bytes
+    with closing(sqlite3.connect(repo.path.as_uri() + '?mode=ro', uri=True)) as restored:
+        assert restored.execute('PRAGMA integrity_check').fetchone() == ('ok',)
+        assert restored.execute('PRAGMA user_version').fetchone() == (4,)
+        original_history = history(restored)
+
+    migrated = target_copy(repo, target, system['protected'])
+    assert migrated.check_integrity()
+    migrated_history = {table: [tuple(row) for row in rows]
+                        for table, rows in migrated.read(history).items()}
+    assert migrated_history == original_history
+    assert repo.path.read_bytes() == source_bytes
```
