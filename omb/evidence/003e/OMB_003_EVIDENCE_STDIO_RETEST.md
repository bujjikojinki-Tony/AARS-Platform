# OMB-003 Evidence 重启与访问范围补验

本轮在 MacBook 使用官方 MCP SDK、真实 stdio 子进程及隔离 SQLite 测试库执行。测试用任务预置合成运行状态，父进程和 MCP 子进程使用同一测试时钟。

- 通过 MCP 关联已登记的合成 Evidence，返回的快照指纹与登记记录一致，`execution_authorized` 为 false。
- 协调器关闭后重新启动，运行标识更新。另一个 MCP 子进程读到同一任务已暂停，并读到原 Evidence 关联事件。事件哈希、Evidence 历史及证据集合指纹一致。
- 另一测试 Bot 查询同一任务事件，收到 `NOT_FOUND_OR_FORBIDDEN`，响应未包含任务数据。
- MCP 适配器测试 4/4 通过。完整回归 330/330 通过，含 32 项 OMB-002-FIX 历史测试。四项冻结输入 SHA-256 一致。

测试入口为 `tests/test_mcp_adapter.py` 中的 `test_sdk_stdio_evidence_event_survives_restart_and_stays_owner_scoped`。本轮为 TM-MAC-04 补充 MCP 和数据库层证据。正式 OpenMausBot 整应用重启后读取 Evidence 仍待验。TM-MCP-08 的 HTML 执行隔离及 Evidence 界面渲染保持 `PARTIAL`。

本机仍无有效 Apple 代码签名身份。按操作者决定暂缓签名配置，003D 为 `BLOCKED_APPROVAL_PLATFORM`，003E 为 `BLOCKED`，003F 和 003G 保持 `HOLD`。总裁决为 `BLOCKED`。

## 测试补丁

```diff
diff --git a/tests/test_mcp_adapter.py b/tests/test_mcp_adapter.py
index da4a02d..12c6738 100644
--- a/tests/test_mcp_adapter.py
+++ b/tests/test_mcp_adapter.py
@@ -7,20 +7,29 @@ import anyio
 from mcp.client import ClientSession
 from mcp.client.stdio import StdioServerParameters, stdio_client
 
-from aars_task_manager import State
+from aars_task_manager import State, TaskRuntime
 from aars_task_manager.mcp_server import ToolAdapter, OPERATIONS
 from tests.support import seed_precondition, key
+from tests.test_evidence_integration import link_args, running_fixture
 
 
-def test_sdk_stdio_initialize_list_call_and_eof(system):
-    manager = system['manager']; repo = system['repo']
+def stdio_launch(system, manager):
+    repo = system['repo']
     # New OS process attaches to the existing coordinator and uses the production serve() adapter.
-    code = ('import anyio,sys; from pathlib import Path; from aars_task_manager import Repository,TaskManager; '
+    code = ('import anyio,sys; from datetime import datetime; from pathlib import Path; '
+            'from aars_task_manager import Repository,TaskManager; from tests.support import FakeClock; '
             'from aars_task_manager.mcp_server import serve; '
             'p=Path(sys.argv[1]); r=Repository.open(p,allowed_root=p.parent,protected_roots=(Path(sys.argv[2]),)); '
-            'anyio.run(serve,TaskManager(r,sys.argv[3],sys.argv[4]))')
-    launch = StdioServerParameters(command=sys.executable, args=['-c',code,str(repo.path),str(system['protected']),manager.binding_id,manager.boot_id],
-                                   env={'PYTHONPATH':os.environ['PYTHONPATH'],'PYTHONDONTWRITEBYTECODE':'1'})
+            'clock=FakeClock(); clock.value=datetime.fromisoformat(sys.argv[5]); '
+            'anyio.run(serve,TaskManager(r,sys.argv[3],sys.argv[4],clock=clock))')
+    return StdioServerParameters(command=sys.executable, args=['-c',code,str(repo.path),str(system['protected']),
+                                                              manager.binding_id,manager.boot_id,system['clock'].now().isoformat()],
+                                 env={'PYTHONPATH':os.environ['PYTHONPATH'],'PYTHONDONTWRITEBYTECODE':'1'})
+
+
+def test_sdk_stdio_initialize_list_call_and_eof(system):
+    manager = system['manager']
+    launch = stdio_launch(system, manager)
     async def run():
         async with stdio_client(launch) as (reader, writer):
             async with ClientSession(reader, writer) as session:
@@ -40,6 +49,51 @@ def test_sdk_stdio_initialize_list_call_and_eof(system):
     assert manager.get(task)['data']['task']['title'] == 'Real stdio draft'
 
 
+def test_sdk_stdio_evidence_event_survives_restart_and_stays_owner_scoped(system):
+    task, attempt, proof = running_fixture(system)
+    task_id = task['task_id']
+    manager = system['manager']
+    evidence_args = link_args(task, attempt, proof['evidence_snapshot_id'])
+
+    async def invoke(actor, name, arguments):
+        with anyio.fail_after(10):
+            async with stdio_client(stdio_launch(system, actor)) as (reader, writer):
+                async with ClientSession(reader, writer) as session:
+                    await session.initialize()
+                    response = await session.call_tool(name, arguments)
+                    payload = json.loads(response.content[0].text)
+                    assert response.is_error == (not payload['ok'])
+                    assert payload['execution_authorized'] is False
+                    return payload
+
+    linked = anyio.run(invoke, manager, 'aars_task_evidence_link_v1', evidence_args)
+    assert linked['ok'], linked.get('error')
+    assert linked['data']['link']['snapshot_id'] == proof['evidence_snapshot_id']
+    trace = manager.evidence_trace(task_id)
+    assert len(trace['history']) == 1
+    system['runtime'].close()
+
+    with TaskRuntime(system['repo'], clock=system['clock']) as runtime:
+        owner = runtime.manager(manager.binding_id)
+        assert owner.boot_id != manager.boot_id
+        recovered = anyio.run(invoke, owner, 'aars_task_get_v1', {'task_id': task_id})
+        assert recovered['ok']
+        assert recovered['data']['task']['state'] == 'PAUSED'
+        assert recovered['data']['attempt'] is None
+        events = anyio.run(invoke, owner, 'aars_task_events_v1', {'task_id': task_id})
+        assert events['ok']
+        linked_events = [event for event in events['data']['events'] if event['event_type'] == 'EVIDENCE_LINKED']
+        assert [event['event_hash'] for event in linked_events] == [trace['history'][0]['event_hash']]
+        after = owner.evidence_trace(task_id)
+        assert after['history'] == trace['history']
+        assert after['evidence_set_hash'] == trace['evidence_set_hash']
+
+        other = runtime.manager(system['other'].binding_id)
+        hidden = anyio.run(invoke, other, 'aars_task_events_v1', {'task_id': task_id})
+        assert hidden['error']['code'] == 'NOT_FOUND_OR_FORBIDDEN'
+        assert 'data' not in hidden
+
+
 def test_locked_start_maps_to_contract_error(system):
     m=system['manager'];t,_=seed_precondition(system['repo'],m,State.READY,system['clock'])
     adapter=ToolAdapter(m)
```
