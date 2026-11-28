# OMB-003 Evidence 摘要候选验收

隔离候选已完成只读 Evidence 摘要。调用 `aars_task_get_v1` 时传入 `include_evidence: true`，可读到关联快照指纹、证据集合指纹和有效使用状态。任务读权限和完整性检查先于摘要查询。省略选项时返回原有结构，MCP 工具数量仍为九项。当前关联最多返回 16 项，超限返回错误。响应范围限于指纹、关联 ID 与状态。

本机用真实 MCP stdio 子进程通过了重启后摘要回读及跨 Bot 拒绝验证。适配器验证了空关联、默认响应、非法选项、过期和撤销状态。整轮回归 332/332 通过，含 32 项历史测试。补丁的 7 个文件有独立的修改前后 SHA-256 清单，且通过 `git apply --check --whitespace=error`。

候选放在独立工作目录。当前 OpenMausBot 正在使用原部署配置。新摘要在正式应用内的渲染、HTML 执行隔离和真人审批仍待验收。复核发现本机有效 Apple 签名身份为 0。OMB-003 总裁决保持 `BLOCKED`。

## 文件指纹

```json
{
  "source_head": "e01610304dda467f2b15f2685b5435f09a35215a",
  "base": "003E local candidate including previous review changes",
  "patch_sha256": "e34cd2a49312f425d6278c6524a6d48fdabccda9355a3dabd33bdbfcdf5729bd",
  "files": {
    "design/omb003a/MCP_INTERFACE_CONTRACT.md": {
      "before": "92d85167f69f25e5b81b3dfd1644e3e397b5271c081ee99e90b1009fdaca3cd6",
      "after": "68cb2909fd396b8891706ee66e0bbab0d44ddf72bc96b5702cebe536794248da"
    },
    "design/omb003a/MCP_RESULT_SCHEMA.json": {
      "before": "ea7c388e424033dabfb28231c7548ad30e608da6b44f512c35ac638fe2e3fd94",
      "after": "7ff977425f3fa16309cdfeb0eb1c1f39e93699491214cea7516dc2c6003c08b7"
    },
    "design/omb003a/MCP_TOOLS_CONTRACT.json": {
      "before": "1fde0bfe8ad0cd5af7ea37e2c02b6bc436f98eb9faf05d3d92da5c4af89040ba",
      "after": "50320fe3438d21dc0fadc8776ff1b82141fd57a3dc7ff70c2417265986a020d9"
    },
    "src/aars_task_manager/evidence.py": {
      "before": "54235bd90024383e2f569c931fa460fb3e9aa2a5f4393032b4387c6ef33cbe08",
      "after": "d1f506908b7fa433c151dd4b32853da4a6fcd74331f0e07570c2fbff9a6c090d"
    },
    "src/aars_task_manager/mcp_server.py": {
      "before": "b1d57eeded06ed31d980ea1ab1dfdf4d122d4e74a31dd2448ac2a22e143cee16",
      "after": "c8b3af4015d5a1f7112950b8af153b17d20ec06b648f15be3cfbdc6d6fbd2df6"
    },
    "src/aars_task_manager/service.py": {
      "before": "aa9818cb8fd16712a812dbe6a4fafdec9f79bc5c20dc9882cc8eae96428998db",
      "after": "5462c115c6adb25a16a4fee10dcebe131196e8ccc909b514c69dd22316f445fe"
    },
    "tests/test_mcp_adapter.py": {
      "before": "0d384ed6c4dad739e10a5b6a8426458773296ac6deb57576cc8349b12cb8d80d",
      "after": "50528110a1d4bff9e9717cc9393d81d164bc0f86c03c47dd30b5140234271ffd"
    }
  }
}
```

## 可应用补丁

```diff
--- a/design/omb003a/MCP_INTERFACE_CONTRACT.md
+++ b/design/omb003a/MCP_INTERFACE_CONTRACT.md
@@ -7,7 +7,7 @@
 |工具|参数要点|语义|
 |---|---|---|
 |aars_task_create_v1|idempotency_key,title,description,purpose|创建DRAFT，owner取可信绑定，无任意owner注入|
-|aars_task_get_v1|task_id|返回摘要/当前version/usage_state，不内联完整Evidence|
+|aars_task_get_v1|task_id，include_evidence（可选布尔值）|返回摘要/当前version/usage_state。显式请求时增加 Evidence 指纹和有效状态，不内联完整 Evidence。|
 |aars_task_list_v1|cursor?,limit≤50,state?|按可见范围、稳定task_id排序分页；游标含版本和过滤hash，篡改拒绝|
 |aars_task_update_v1|task_id,expected_version,idempotency_key,patch|仅DRAFT，白名单title/description/priority/due_at；不接受任意JSON patch路径|
 |aars_task_transition_v1|task_id,expected_version,idempotency_key,action,reason?,attempt_id?,fencing_token?|只允许Bot动作start/pause/fail/cancel；状态机决定权限，不能传目标state|
@@ -34,6 +34,8 @@
 
 MCP_RESULT_SCHEMA.json优先于前文简化样例。create/get/update/transition/lease/link/review统一返回data={task:完整规范化Task,attempt:当前Attempt或null,review:ReviewRequest或null,link:本次Link或null}；TaskView不包含签名receipt或原始nonce。list返回data={tasks:TaskSummary[],next_cursor:string|null}；events返回data={events:EventSummary[],next_after_seq:integer|null}。页内严格字节限额；同状态变更仍返回新的version。分页只读请求replayed=false。
 
+`aars_task_get_v1` 接受可选的 `include_evidence: true`。当前任务的读权限与完整性校验通过后，响应增加 `data.evidence_summary`，包含 `evidence_set_hash` 和最多 16 个当前关联。各关联仅返回 `link_id`、`snapshot_id`、`effective_use_state`。没有关联时返回空列表和零指纹，超限按现有响应大小约束拒绝。指纹对应已持久化的证据集合，有效状态反映查询时已知的授权期限或撤销情况。省略选项或传入 `false` 时，响应保留原结构。
+
 review中的nonce_hash仅是不可逆核对值，不可替代nonce或授权；签名/receipt不通过这些工具提供。错误允许码以MCP_RESULT_SCHEMA.json枚举为准，其中NOT_FOUND_OR_FORBIDDEN同时用于不存在和无权限；避免向未授权调用者暴露current_version。
 
 create默认priority=3、due_at=null、supersedes_task_id=null。transition的start禁止携旧attempt/fencing；pause/fail必需两者，RUNNING下cancel也必须携两者（依赖当前状态的规则由语义验证器执行），非RUNNING cancel不得携无关租约。reason在fail/pause/cancel必填。RPC错误保留协议层语法错误；业务拒绝按isError封装。
--- a/design/omb003a/MCP_RESULT_SCHEMA.json
+++ b/design/omb003a/MCP_RESULT_SCHEMA.json
@@ -1095,6 +1095,31 @@
       ],
       "additionalProperties": false
     },
+    "EvidenceSummary": {
+      "type": "object",
+      "properties": {
+        "evidence_set_hash": {
+          "type": "string",
+          "pattern": "^sha256:[0-9a-f]{64}$"
+        },
+        "current": {
+          "type": "array",
+          "maxItems": 16,
+          "items": {
+            "type": "object",
+            "properties": {
+              "link_id": {"type": "string", "pattern": "^link\\.[0-9a-f]{32}$"},
+              "snapshot_id": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
+              "effective_use_state": {"enum": ["USABLE_FIXTURE", "REVIEW_REQUIRED", "REVOKED"]}
+            },
+            "required": ["link_id", "snapshot_id", "effective_use_state"],
+            "additionalProperties": false
+          }
+        }
+      },
+      "required": ["evidence_set_hash", "current"],
+      "additionalProperties": false
+    },
     "TaskView": {
       "type": "object",
       "properties": {
@@ -1130,6 +1155,9 @@
               "type": "null"
             }
           ]
+        },
+        "evidence_summary": {
+          "$ref": "#/$defs/EvidenceSummary"
         }
       },
       "required": [
--- a/design/omb003a/MCP_TOOLS_CONTRACT.json
+++ b/design/omb003a/MCP_TOOLS_CONTRACT.json
@@ -133,6 +133,10 @@
           "task_id": {
             "type": "string",
             "pattern": "^task\\.[0-9a-f]{32}$"
+          },
+          "include_evidence": {
+            "type": "boolean",
+            "description": "If true, include a bounded summary of linked Evidence fingerprints and use states."
           }
         },
         "required": [
--- a/src/aars_task_manager/evidence.py
+++ b/src/aars_task_manager/evidence.py
@@ -245,6 +245,27 @@
             raise TaskError('INTEGRITY_FAILURE')
 
 
+def current_link_summaries(db, task, now, graph, links):
+    usable = grant_usable(db, graph, now)
+    revoked = revocation(db, task.workspace_id)
+    current = []
+    for row in links:
+        effective = row['use_state']
+        if effective == 'USABLE_FIXTURE' and not usable:
+            effective = 'REVOKED' if revoked else 'REVIEW_REQUIRED'
+        current.append({'link_id': row['link_id'], 'snapshot_id': row['snapshot_id'],
+                        'effective_use_state': effective})
+    return current
+
+
+def read_summary(db, task, now):
+    links = latest_links(link_versions(db, task))
+    if len(links) > 16:
+        raise TaskError('RESPONSE_TOO_LARGE')
+    current = current_link_summaries(db, task, now, verified_graph(db, task.workspace_id), links) if links else []
+    return {'evidence_set_hash': evidence_digest(links), 'current': current}
+
+
 def trace(db, task, now):
     graph = verified_graph(db, task.workspace_id)
     result = []
@@ -260,15 +281,10 @@
         record = json.loads(object_row['canonical_json'])
         provenance = {'evidence_object_id': object_row['object_id'], 'observation_ids': record['observation_ids'],
             'core_provenance': record['provenance'], 'archive_entry': FIXTURE_ARCHIVE_ENTRY}
-    current = []
-    revoked = revocation(db, task.workspace_id)
-    for row in latest_links(result):
-        effective = row['use_state']
-        if effective == 'USABLE_FIXTURE' and not grant_usable(db, graph, now):
-            effective = 'REVOKED' if revoked else 'REVIEW_REQUIRED'
-        current.append({'link_id': row['link_id'], 'snapshot_id': row['snapshot_id'], 'effective_use_state': effective})
-    return {'task_id': task.task_id, 'version': task.version, 'history': result, 'current': current,
+    links = latest_links(result)
+    return {'task_id': task.task_id, 'version': task.version, 'history': result,
+            'current': current_link_summaries(db, task, now, graph, links) if links else [],
             'source': None if not graph or not result else {'artifact_sha256': graph['artifact_hash'],
                 'graph_digest': graph['graph_digest'], 'grant_hash': graph['grant_hash'], 'expires_at': graph['expires_at'],
                 'source_verification': 'FIXTURE_VERIFIED', 'license_basis': LICENSE_BASIS},
-            'evidence_set_hash': evidence_digest(latest_links(result)), 'provenance': provenance, 'execution_authorized': False}
+            'evidence_set_hash': evidence_digest(links), 'provenance': provenance, 'execution_authorized': False}
--- a/src/aars_task_manager/mcp_server.py
+++ b/src/aars_task_manager/mcp_server.py
@@ -29,7 +29,7 @@
 MAX_WIRE_BYTES = 64 * 1024
 OPERATIONS = {
     'aars_task_create_v1': ('create', 'Create a task draft within the assigned workspace.'),
-    'aars_task_get_v1': ('get', 'Read a task and its pending review summary.'),
+    'aars_task_get_v1': ('get', 'Read a task and its pending review summary; optionally include Evidence fingerprints and use states.'),
     'aars_task_list_v1': ('list', 'List visible tasks, using continuation cursors.'),
     'aars_task_update_v1': ('update', 'Edit a draft using its expected version.'),
     'aars_task_transition_v1': ('transition', 'Request an allowed task transition. Starts require operator approval.'),
--- a/src/aars_task_manager/service.py
+++ b/src/aars_task_manager/service.py
@@ -46,7 +46,9 @@
     def execute(self,operation,arguments):
         if not isinstance(operation,str):raise TaskError('INVALID_ARGUMENT')
         if operation in OPERATOR_ACTIONS:raise TaskError('APPROVAL_LOCKED')
-        if operation=='get':return self.get(**self._read_args(arguments,{'task_id'}))
+        if operation=='get':
+            request_shape(arguments,('task_id',),('include_evidence',))
+            return self.get(**arguments)
         if operation=='list':
             request_shape(arguments,(),('state','limit','cursor'));return self.list_tasks(**arguments)
         if operation=='events':
@@ -153,10 +155,6 @@
             return response
         return self.repository.write(change)
 
-    @staticmethod
-    def _read_args(arguments,required):
-        request_shape(arguments,required);return arguments
-
     def _lease(self,db,task,p,args,now):
         require_id(args.get('attempt_id'),'attempt');require_version(args.get('fencing_token'))
         attempt=db.execute("SELECT * FROM attempts WHERE workspace_id=? AND task_id=? AND status IN ('ACQUIRED','RUNNING')",(task.workspace_id,task.task_id)).fetchone()
@@ -176,15 +174,20 @@
                 return 'REVIEW_REQUIRED'
         return task.usage_state
 
-    def get(self,task_id):
+    def get(self,task_id,*,include_evidence=False):
         require_id(task_id,'task')
+        if type(include_evidence) is not bool:
+            raise TaskError('INVALID_ARGUMENT')
         def read(db):
             p=self._principal(db,'task.read');task=self.repository.task(db,task_id,p)
             review=reviews.current(db,task) if task.state==State.REVIEW_PENDING else None
             if review and (status:=reviews.invalidation_reason(db,task,self._now(task))):
                 review={**review,'status':status}
             data = self._view(task, review=review)
-            data['task']['usage_state'] = self._current_usage(db, task, self._now())
+            now = self._now(task) if include_evidence else self._now()
+            data['task']['usage_state'] = self._current_usage(db, task, now)
+            if include_evidence:
+                data['evidence_summary'] = evidence.read_summary(db, task, now)
             return self._envelope(data)
         return self.repository.read(read)
 
--- a/tests/test_mcp_adapter.py
+++ b/tests/test_mcp_adapter.py
@@ -2,12 +2,14 @@
 from pathlib import Path
 import os
 import sys
+from datetime import timedelta
 
 import anyio
 from mcp.client import ClientSession
 from mcp.client.stdio import StdioServerParameters, stdio_client
 
 from aars_task_manager import State, TaskRuntime
+from aars_task_manager.domain import ZERO_HASH, stamp
 from aars_task_manager.mcp_server import ToolAdapter, OPERATIONS
 from tests.support import create, seed_precondition, key
 from tests.test_evidence_integration import link_args, running_fixture
@@ -87,11 +89,51 @@
         after = owner.evidence_trace(task_id)
         assert after['history'] == trace['history']
         assert after['evidence_set_hash'] == trace['evidence_set_hash']
+        assert 'evidence_summary' not in recovered['data']
+        evidence_args = {'task_id': task_id, 'include_evidence': True}
+        summary = anyio.run(invoke, owner, 'aars_task_get_v1', evidence_args)
+        assert summary['data']['evidence_summary'] == {
+            'current': trace['current'], 'evidence_set_hash': trace['evidence_set_hash'],
+        }
+        assert summary['data']['link'] is None
 
         other = runtime.manager(system['other'].binding_id)
         hidden = anyio.run(invoke, other, 'aars_task_events_v1', {'task_id': task_id})
         assert hidden['error']['code'] == 'NOT_FOUND_OR_FORBIDDEN'
         assert 'data' not in hidden
+        denied = anyio.run(invoke, other, 'aars_task_get_v1', evidence_args)
+        assert denied['error']['code'] == 'NOT_FOUND_OR_FORBIDDEN'
+        assert 'data' not in denied
+
+
+def test_evidence_summary_reports_effective_use_without_exposing_records(system):
+    adapter = ToolAdapter(system['manager'])
+    tool = 'aars_task_get_v1'
+    draft = create(system['manager'])
+    draft_args = {'task_id': draft['task_id']}
+    default = adapter.call(tool, draft_args)['data']
+    assert default == adapter.call(tool, {**draft_args, 'include_evidence': False})['data']
+    assert 'evidence_summary' not in default
+    empty = adapter.call(tool, {**draft_args, 'include_evidence': True})
+    assert empty['data']['evidence_summary'] == {'current': [], 'evidence_set_hash': ZERO_HASH}
+    assert adapter.call(tool, {**draft_args, 'include_evidence': 'true'})['error']['code'] == 'INVALID_ARGUMENT'
+
+    expiry = stamp(system['clock'].now() + timedelta(seconds=30))
+    task, attempt, proof = running_fixture(system, expires_at=expiry)
+    system['manager'].execute('evidence_link', link_args(task, attempt, proof['evidence_snapshot_id']))
+    args = {'task_id': task['task_id'], 'include_evidence': True}
+    before = adapter.call(tool, args)
+    first = before['data']['evidence_summary']
+    assert [link['effective_use_state'] for link in first['current']] == ['USABLE_FIXTURE']
+    assert before['execution_authorized'] is False
+    system['clock'].advance(31)
+    expired = adapter.call(tool, args)['data']['evidence_summary']
+    assert expired['evidence_set_hash'] == first['evidence_set_hash']
+    assert [link['effective_use_state'] for link in expired['current']] == ['REVIEW_REQUIRED']
+    assert system['runtime'].revoke_frozen_fixture('synthetic withdrawal') == 1
+    revoked = adapter.call(tool, args)['data']['evidence_summary']
+    assert [link['effective_use_state'] for link in revoked['current']] == ['REVOKED']
+    assert revoked['current'][0]['snapshot_id'] == proof['evidence_snapshot_id']
 
 
 def test_sdk_stdio_concurrent_updates_commit_once_and_keep_owner_boundary(system):
```
