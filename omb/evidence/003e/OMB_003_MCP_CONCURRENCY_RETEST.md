# OMB-003 MCP 并发写入补验

新增 `test_sdk_stdio_concurrent_updates_commit_once_and_keep_owner_boundary`。在 MacBook 上用官方 MCP SDK 和隔离 SQLite，启动三个独立 stdio 服务进程。完成握手后同时发送针对同一草稿版本 1 的更新。

拥有者的两个会话共用既有绑定。一条更新成功，另一条收到 `VERSION_CONFLICT`。第三个会话使用有更新能力的另一 Bot 绑定，收到 `NOT_FOUND_OR_FORBIDDEN`，且响应未包含任务数据。数据库最终为获胜更新的 `DRAFT` 版本 2，仅含一条创建事件和一条更新事件，完整性检查通过。

新增用例通过，完整回归 331/331 通过，含 32 项历史测试。四项冻结输入 SHA-256 匹配。

TM-MAC-05 获得真实进程层并发及归属验证证据。两个不同 Bot 绑定对同一草稿的结果受现有归属规则限制。此轮没有在 OpenMausBot 应用内发起并发轮次，正式实机门与 OMB-003 总裁决维持 `BLOCKED`。

## 叠加测试补丁

此补丁包含上一轮 Evidence 回读测试和本轮并发测试，适用于两项补验之前的源码快照。

```diff
diff --git a/tests/test_mcp_adapter.py b/tests/test_mcp_adapter.py
index da4a02d..130526b 100644
--- a/tests/test_mcp_adapter.py
+++ b/tests/test_mcp_adapter.py
@@ -7,20 +7,29 @@ import anyio
 from mcp.client import ClientSession
 from mcp.client.stdio import StdioServerParameters, stdio_client
 
-from aars_task_manager import State
+from aars_task_manager import State, TaskRuntime
 from aars_task_manager.mcp_server import ToolAdapter, OPERATIONS
-from tests.support import seed_precondition, key
+from tests.support import create, seed_precondition, key
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
@@ -40,6 +49,101 @@ def test_sdk_stdio_initialize_list_call_and_eof(system):
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
+def test_sdk_stdio_concurrent_updates_commit_once_and_keep_owner_boundary(system):
+    owner = system['manager']
+    other = system['other']
+    draft = create(owner)
+    task_id = draft['task_id']
+
+    async def race():
+        cases = {'first': owner, 'second': owner, 'other': other}
+        ready = {label: anyio.Event() for label in cases}
+        release = anyio.Event()
+        results = {}
+
+        async def update(label, actor):
+            async with stdio_client(stdio_launch(system, actor)) as (reader, writer):
+                async with ClientSession(reader, writer) as session:
+                    await session.initialize()
+                    ready[label].set()
+                    await release.wait()
+                    response = await session.call_tool('aars_task_update_v1', {
+                        'task_id': task_id, 'expected_version': 1,
+                        'idempotency_key': key(), 'patch': {'title': label},
+                    })
+                    payload = json.loads(response.content[0].text)
+                    assert response.is_error == (not payload['ok'])
+                    assert payload['execution_authorized'] is False
+                    results[label] = payload
+
+        with anyio.fail_after(15):
+            async with anyio.create_task_group() as group:
+                for label, actor in cases.items():
+                    group.start_soon(update, label, actor)
+                for initialized in ready.values():
+                    await initialized.wait()
+                release.set()
+        return results
+
+    results = anyio.run(race)
+    winner, = [label for label in ('first', 'second') if results[label]['ok']]
+    loser, = [label for label in ('first', 'second') if label != winner]
+    assert results[loser]['error']['code'] == 'VERSION_CONFLICT'
+    assert results['other']['error']['code'] == 'NOT_FOUND_OR_FORBIDDEN'
+    assert 'data' not in results['other']
+    saved = owner.get(task_id)['data']['task']
+    assert saved == results[winner]['data']['task']
+    assert (saved['state'], saved['version'], saved['title']) == ('DRAFT', 2, winner)
+    events = owner.events(task_id)['data']['events']
+    assert [(event['seq'], event['event_type']) for event in events] == [(1, 'CREATED'), (2, 'UPDATED')]
+    assert system['repo'].check_integrity()
+
+
 def test_locked_start_maps_to_contract_error(system):
     m=system['manager'];t,_=seed_precondition(system['repo'],m,State.READY,system['clock'])
     adapter=ToolAdapter(m)
```
