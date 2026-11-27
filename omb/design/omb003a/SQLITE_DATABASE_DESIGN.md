# WP-05 SQLite 隔离与一致性设计

此处DDL为设计文本，未执行。未来开发库建议work/omb003-dev/runtime/task_manager.dev.sqlite，回归测试使用独立临时目录，实机验收库再单独建立。必须拒绝路径与002证据库、其符号/硬链接、真实路径或device/inode相同；不能只检查文件名是否不同。003服务不得接受MCP传入的db_path。目录0700、文件0600；连接逐请求创建/关闭，线程不共享Connection。

连接策略：foreign_keys=ON；新003库application_id=0x4F4D4233，user_version从1开始；journal_mode=DELETE、synchronous=FULL、busy_timeout=500ms；验证读回值。现有SQLite3.50.4不启用WAL，参见[官方WAL说明](https://www.sqlite.org/wal.html)。新库启动发现非空application_id不符、schema_version过新、权限不符或未知表结构均拒绝，不自动改造。冻结002库的tasks表仅为fixture索引，禁止原地升级。

## 逻辑DDL草案

所有时间存为带Z的UTC字符串，由服务校验格式/时序。示意中status/domain约束的允许值必须与元模型和JSON契约相同，不由DB接受任意字符串后再推断权限。

```sql
CREATE TABLE workspaces (
 workspace_id TEXT PRIMARY KEY, db_instance_id TEXT NOT NULL UNIQUE,
 mode TEXT NOT NULL CHECK(mode IN ('LOCAL_SYNTHETIC','CATALOG_METADATA')),
 policy_version INTEGER NOT NULL CHECK(policy_version>=1), created_at TEXT NOT NULL
);
CREATE TABLE principals (
 workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id), principal_id TEXT NOT NULL,
 kind TEXT NOT NULL CHECK(kind IN ('BOT','OPERATOR','SERVICE')),
 binding_id TEXT NOT NULL, binding_version INTEGER NOT NULL CHECK(binding_version>=1),
 active INTEGER NOT NULL CHECK(active IN (0,1)), capabilities_json TEXT NOT NULL CHECK(json_valid(capabilities_json)),
 PRIMARY KEY(workspace_id,principal_id), UNIQUE(workspace_id,binding_id)
);
CREATE TABLE tm_tasks (
 workspace_id TEXT NOT NULL, task_id TEXT NOT NULL, owner_principal_id TEXT NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('DRAFT','READY','RUNNING','PAUSED','REVIEW_PENDING','COMPLETED','REJECTED','FAILED','CANCELLED')),
 version INTEGER NOT NULL CHECK(version>=1), definition_revision INTEGER NOT NULL CHECK(definition_revision>=1),
 definition_hash TEXT NOT NULL, definition_json TEXT NOT NULL CHECK(json_valid(definition_json)),
 usage_state TEXT NOT NULL CHECK(usage_state IN ('USABLE','REVIEW_REQUIRED','UNUSABLE')),
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 PRIMARY KEY(workspace_id,task_id),
 FOREIGN KEY(workspace_id,owner_principal_id) REFERENCES principals(workspace_id,principal_id)
);
CREATE TABLE task_events (
 workspace_id TEXT NOT NULL, task_id TEXT NOT NULL, seq INTEGER NOT NULL CHECK(seq>=1), event_id TEXT NOT NULL UNIQUE,
 actor_principal_id TEXT NOT NULL, event_type TEXT NOT NULL, at TEXT NOT NULL,
 from_version INTEGER NOT NULL, to_version INTEGER NOT NULL CHECK(to_version=from_version+1),
 from_state TEXT, to_state TEXT NOT NULL, payload_json TEXT NOT NULL CHECK(json_valid(payload_json)),
 payload_hash TEXT NOT NULL, prev_hash TEXT NOT NULL, event_hash TEXT NOT NULL,
 PRIMARY KEY(workspace_id,task_id,seq), UNIQUE(workspace_id,task_id,to_version),
 FOREIGN KEY(workspace_id,task_id) REFERENCES tm_tasks(workspace_id,task_id),
 FOREIGN KEY(workspace_id,actor_principal_id) REFERENCES principals(workspace_id,principal_id)
);
CREATE TABLE task_revisions (
 workspace_id TEXT NOT NULL, task_id TEXT NOT NULL, version INTEGER NOT NULL, event_id TEXT NOT NULL REFERENCES task_events(event_id),
 snapshot_json TEXT NOT NULL CHECK(json_valid(snapshot_json)), snapshot_hash TEXT NOT NULL,
 PRIMARY KEY(workspace_id,task_id,version),
 FOREIGN KEY(workspace_id,task_id) REFERENCES tm_tasks(workspace_id,task_id)
);
CREATE TABLE attempts (
 workspace_id TEXT NOT NULL, task_id TEXT NOT NULL, attempt_id TEXT NOT NULL UNIQUE,
 attempt_no INTEGER NOT NULL CHECK(attempt_no>=1), fencing_token INTEGER NOT NULL CHECK(fencing_token>=1),
 actor_principal_id TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('ACQUIRED','RUNNING','SUBMITTED','PAUSED','FAILED','EXPIRED','CANCELLED')),
 boot_id TEXT NOT NULL, lease_expires_at TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT,
 PRIMARY KEY(workspace_id,task_id,attempt_no), UNIQUE(workspace_id,task_id,fencing_token),
 FOREIGN KEY(workspace_id,task_id) REFERENCES tm_tasks(workspace_id,task_id),
 FOREIGN KEY(workspace_id,actor_principal_id) REFERENCES principals(workspace_id,principal_id)
);
CREATE UNIQUE INDEX one_live_attempt ON attempts(workspace_id,task_id) WHERE status IN ('ACQUIRED','RUNNING');
CREATE TABLE object_snapshots (
 workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id), snapshot_id TEXT NOT NULL,
 object_id TEXT NOT NULL, object_type TEXT NOT NULL, canonical_json TEXT NOT NULL CHECK(json_valid(canonical_json)),
 graph_digest TEXT NOT NULL, source_verification TEXT NOT NULL, source_record_json TEXT NOT NULL CHECK(json_valid(source_record_json)),
 created_at TEXT NOT NULL, PRIMARY KEY(workspace_id,snapshot_id), UNIQUE(workspace_id,object_id,snapshot_id)
);
CREATE TABLE evidence_link_versions (
 workspace_id TEXT NOT NULL, task_id TEXT NOT NULL, link_id TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>=1),
 snapshot_id TEXT NOT NULL, scope_json TEXT NOT NULL CHECK(json_valid(scope_json)), purpose TEXT NOT NULL,
 use_state TEXT NOT NULL CHECK(use_state IN ('USABLE_FIXTURE','REVIEW_REQUIRED','UNUSABLE','REVOKED')),
 verification_record_json TEXT NOT NULL CHECK(json_valid(verification_record_json)), event_id TEXT NOT NULL REFERENCES task_events(event_id),
 PRIMARY KEY(workspace_id,task_id,link_id,revision),
 FOREIGN KEY(workspace_id,task_id) REFERENCES tm_tasks(workspace_id,task_id),
 FOREIGN KEY(workspace_id,snapshot_id) REFERENCES object_snapshots(workspace_id,snapshot_id)
);
CREATE TABLE review_requests (
 workspace_id TEXT NOT NULL, task_id TEXT NOT NULL, review_id TEXT NOT NULL UNIQUE,
 kind TEXT NOT NULL CHECK(kind IN ('PLAN','RESULT','CONTROL')), subject_version INTEGER NOT NULL,
 definition_hash TEXT NOT NULL, evidence_set_hash TEXT NOT NULL, snapshot_json TEXT NOT NULL CHECK(json_valid(snapshot_json)),
 action TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('PENDING','APPROVED','REJECTED','CHANGES_REQUESTED','STALE','EXPIRED')),
 nonce_hash TEXT NOT NULL UNIQUE, expires_at TEXT NOT NULL, created_at TEXT NOT NULL,
 PRIMARY KEY(workspace_id,task_id,review_id), FOREIGN KEY(workspace_id,task_id) REFERENCES tm_tasks(workspace_id,task_id)
);
CREATE UNIQUE INDEX one_pending_review ON review_requests(workspace_id,task_id) WHERE status='PENDING';
CREATE TABLE approval_decisions (
 approval_id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL, task_id TEXT NOT NULL, review_id TEXT NOT NULL UNIQUE,
 decision TEXT NOT NULL CHECK(decision IN ('APPROVE_PLAN','APPROVE_RESULT','REJECT_RESULT','REQUEST_CHANGES','AUTHORIZE_CONTROL')),
 actor_principal_id TEXT NOT NULL, signer_key_id TEXT NOT NULL, receipt_json TEXT NOT NULL CHECK(json_valid(receipt_json)),
 receipt_sha256 TEXT NOT NULL, decided_at TEXT NOT NULL,
 FOREIGN KEY(workspace_id,task_id,review_id) REFERENCES review_requests(workspace_id,task_id,review_id),
 FOREIGN KEY(workspace_id,actor_principal_id) REFERENCES principals(workspace_id,principal_id)
);
CREATE TABLE idempotency_records (
 workspace_id TEXT NOT NULL, principal_id TEXT NOT NULL, idem_key TEXT NOT NULL,
 method TEXT NOT NULL, request_hash TEXT NOT NULL, response_json TEXT NOT NULL CHECK(json_valid(response_json)),
 result_version INTEGER, created_at TEXT NOT NULL,
 PRIMARY KEY(workspace_id,principal_id,idem_key),
 FOREIGN KEY(workspace_id,principal_id) REFERENCES principals(workspace_id,principal_id)
);
CREATE INDEX task_owner_state ON tm_tasks(workspace_id,owner_principal_id,state,task_id);
CREATE INDEX evidence_lookup ON evidence_link_versions(workspace_id,snapshot_id,task_id);
```

DDL不能单独保证对象类型、哈希真实性、时间格式或合法状态转换；由同一聚合服务校验，测试矩阵覆盖绕过上层的失败。approval_decisions的actor必须在服务内核实为该review工作区的OPERATOR，不能因为表中存了一个principal字符串就信任。所有FK的删除策略默认RESTRICT，不做CASCADE删除追溯记录。

## 写事务

1. 解析并限制请求；解析可信启动身份，核查当前绑定/用途/范围。
2. BEGIN IMMEDIATE；再次读取绑定和策略。SQLite仍只有一个writer，不能把事务或RLock说成多writer并行能力。[事务依据](https://www.sqlite.org/lang_transaction.html)。
3. 查幂等键；同键同请求且仍可访问时回放；同键异请求拒绝。
4. SELECT当前Task；核对expected_version；校验状态、租约、fencing、Evidence与review digest。拒绝路径不修改Task。
5. UPDATE tm_tasks ... SET version=version+1 ... WHERE workspace_id=? AND task_id=? AND version=?；rowcount必须1。按同一事务追加event、revision、attempt/link/review、幂等结果；唯一约束作为最后防线。
6. COMMIT成功后才返回成功。不在事务中调用模型、网络、人工交互或长时间认证。异常显式ROLLBACK，finally关闭Connection；锁等待按MCP契约有界重试。

创建Task先插入version=1任务，首事件from_version=0、to_version=1、seq=1，再插revision与幂等结果，同一事务提交。其他变更含绑定撤销引起的usage失效，亦使用CAS和事件追加。事件seq与版本保持一致；service校验event actor与实际可信主体一致。

事件是可核对审计，不声称恰好一次外部副作用：只有数据库状态、事件与幂等记录在同一提交内。003C若要外发事件，必须另审outbox/至少一次投递/消费方去重，不能在此设计里宣称跨系统原子性已实现。

## 恢复、迁移、回滚

启动先校验application_id/user_version/integrity_check、schema指纹、Task/revision/event链和对象hash。发现损坏进入只读隔离，禁止“自动修复并批准”。上次boot_id的活动attempt到期或失效后以明确恢复事件转PAUSED，新任务版本和fencing不复用。

迁移只允许操作者离线维护，停止003写入，SQLite backup API创建一致备份，校验SHA256和quick_check；在新副本执行迁移，失败丢弃副本。禁止复制正在写的裸.db作为唯一备份，禁止ATTACH冻结库参与写事务。回滚采用“旧二进制+旧schema备份”，不逆向DROP列，不让旧程序读取新schema；新事件先归档，显式说明回滚时间点后的任务记录不会被当成已恢复。

002不受迁移影响：新launcher、新venv、新DB、新MCP名称、新专用003测试Bot；003F才允许操作者切换。撤回003时停用其服务器并恢复002原启动器，核验002包hash/工具/既有9对象，保留003失败日志。不能以“回滚”覆盖002数据或清空003追溯。

## DDL完整性补充：Task ACL与审批主体

```sql
CREATE TABLE task_acl (
 workspace_id TEXT NOT NULL, task_id TEXT NOT NULL, principal_id TEXT NOT NULL,
 permission TEXT NOT NULL CHECK(permission IN ('READ','PROPOSE','WORK')),
 active INTEGER NOT NULL CHECK(active IN (0,1)), granted_by TEXT NOT NULL,
 grant_event_id TEXT NOT NULL REFERENCES task_events(event_id),
 PRIMARY KEY(workspace_id,task_id,principal_id,permission),
 FOREIGN KEY(workspace_id,task_id) REFERENCES tm_tasks(workspace_id,task_id),
 FOREIGN KEY(workspace_id,principal_id) REFERENCES principals(workspace_id,principal_id),
 FOREIGN KEY(workspace_id,granted_by) REFERENCES principals(workspace_id,principal_id)
);
```

approval_decisions已携带workspace_id、task_id并使用复合FK约束review及审批主体，禁止仅靠review_id串联不同工作区。task_acl可更新当前投影，但所有grant/revoke事件和Revision必须保留；只有OPERATOR可作此变更。ACL的scope hash和policy_version必须进入review snapshot。

错误缓存与拒绝审计不生成Task版本事件；如需要记录安全拒绝，使用独立append-only security_audit设计，不伪造任务状态变更。幂等键不自动按时间淘汰，工作区归档可保留request_hash/result tombstone以防重新执行。

重启恢复还必须使所有未消费review challenge失效：RESULT review失效对应REVIEW_PENDING→PAUSED；PLAN/CONTROL只记录失效同状态事件，不自动把DRAFT/READY变为批准。恢复事务同时保留历史review/receipt，不重新使用旧boot的nonce、租约或缓存批准结果。
