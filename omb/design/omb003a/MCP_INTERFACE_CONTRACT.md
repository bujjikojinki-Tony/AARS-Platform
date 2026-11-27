# WP-04 MCP 接口契约

旧5工具aars_health、aars_graph_certify、aars_fixture_store、aars_evidence_query、aars_task_objects的名称、参数、返回语义和合成限制全部保持。旧OMB-SIM任务ID是fixture namespace，与新Task管理ID无隐式转换。新工具仅在未来独立aars-task-dev服务中出现；002 aars-local不添加工具。

新增草案见MCP_TOOLS_CONTRACT.json，所有inputSchema additionalProperties=false；客户端校验之外服务端再次校验。schema_version固定omb-task/1.0；协议版本由官方SDK协商，不沿用手写Session。拒绝未知字段actor_id、bot_id、approved、db_path、license_pass等。读取通过服务端PrincipalBinding过滤；枚举到工具不等于拥有调用权限。

|工具|参数要点|语义|
|---|---|---|
|aars_task_create_v1|idempotency_key,title,description,purpose|创建DRAFT，owner取可信绑定，无任意owner注入|
|aars_task_get_v1|task_id|返回摘要/当前version/usage_state，不内联完整Evidence|
|aars_task_list_v1|cursor?,limit≤50,state?|按可见范围、稳定task_id排序分页；游标含版本和过滤hash，篡改拒绝|
|aars_task_update_v1|task_id,expected_version,idempotency_key,patch|仅DRAFT，白名单title/description/priority/due_at；不接受任意JSON patch路径|
|aars_task_transition_v1|task_id,expected_version,idempotency_key,action,reason?,attempt_id?,fencing_token?|只允许Bot动作start/pause/fail/cancel；状态机决定权限，不能传目标state|
|aars_task_lease_renew_v1|task_id,expected_version,idempotency_key,attempt_id,fencing_token|有效当前Bot租约才能续租；返回新version与expires_at|
|aars_task_evidence_link_v1|task_id,expected_version,idempotency_key,attempt_id,fencing_token,snapshot_id|只链接事先由可信适配器登记并验证的Core Evidence；不接收对象正文/文件路径|
|aars_task_review_request_v1|task_id,expected_version,idempotency_key,attempt_id,fencing_token|RUNNING到REVIEW_PENDING；服务端生成review snapshot与digest，不能指定批准状态|
|aars_task_events_v1|task_id,after_seq≥0,limit≤50|只读、按seq分页；校验哈希链，跨范围拒绝|

没有approve/reject/operator工具。MCP工具注释readOnlyHint等只是提示，不能授予权限。规范参考：[MCP Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)。

成功content[0].text为完整JSON envelope：
```json
{"schema_version":"omb-task/1.0","ok":true,"request_id":"request.<32hex>","replayed":false,"data":{"task_id":"task.<32hex>","version":2,"state":"READY"},"execution_authorized":false}
```
失败为isError=true，content文本JSON含ok=false、error.code、message、retryable、request_id、execution_authorized=false。示例占位ID不是合法实际ID。常见码：INVALID_ARGUMENT、NOT_FOUND_OR_FORBIDDEN（避免泄露跨范围存在性）、VERSION_CONFLICT、IDEMPOTENCY_CONFLICT、INVALID_TRANSITION、LEASE_EXPIRED、FENCING_CONFLICT、REVIEW_STALE、EVIDENCE_UNUSABLE、INTEGRITY_FAILURE、DB_BUSY、INTERNAL_ERROR。失败不回传堆栈、SQL或本地路径。缺expected_version不能默认为当前版本。

请求最大16KiB UTF-8，文本响应最大16KiB；列表按字节和条数双限分页。事件payload只返回摘要和digest，无任意文件/URL读取。摘要文本过长返回显式truncated=true和可续页游标，不能静默截断JSON。每页含next_cursor/null；读取应在单个只读事务内取一致快照。稳定过滤游标在10分钟或workspace generation变更后失效；失效返回CURSOR_EXPIRED，客户端重新读取。

幂等键为UUID，由调用者提供，不是JSON-RPC request id。canonical request hash包括方法、workspace、trusted principal、完整参数（含expected_version，排除key自身与传输request id）。先核查绑定和基本访问权限，再查幂等记录；同key同hash返回原结果及replayed=true，不能当作当前状态；同key异hash拒绝。新版本重试必须使用新key。传输中断后只用原key查询/重试，不能改key盲重放。

全事务超时5秒：busy_timeout=500ms，最多3次带抖动重试（50/100/200ms），重试重开事务并重新授权、校验版本。VERSION_CONFLICT不自动变成覆盖；结果未知的COMMIT不能当作失败重放。业务确定性错误可缓存原错误；DB_BUSY/传输超时不缓存为永久结果。

## 返回结构定稿

MCP_RESULT_SCHEMA.json优先于前文简化样例。create/get/update/transition/lease/link/review统一返回data={task:完整规范化Task,attempt:当前Attempt或null,review:ReviewRequest或null,link:本次Link或null}；TaskView不包含签名receipt或原始nonce。list返回data={tasks:TaskSummary[],next_cursor:string|null}；events返回data={events:EventSummary[],next_after_seq:integer|null}。页内严格字节限额；同状态变更仍返回新的version。分页只读请求replayed=false。

review中的nonce_hash仅是不可逆核对值，不可替代nonce或授权；签名/receipt不通过这些工具提供。错误允许码以MCP_RESULT_SCHEMA.json枚举为准，其中NOT_FOUND_OR_FORBIDDEN同时用于不存在和无权限；避免向未授权调用者暴露current_version。

create默认priority=3、due_at=null、supersedes_task_id=null。transition的start禁止携旧attempt/fencing；pause/fail必需两者，RUNNING下cancel也必须携两者（依赖当前状态的规则由语义验证器执行），非RUNNING cancel不得携无关租约。reason在fail/pause/cancel必填。RPC错误保留协议层语法错误；业务拒绝按isError封装。

CATALOG_METADATA仅可创建目录DRAFT并读取/编辑/取消；不能进入可运行状态。服务端按purpose拒绝非法动作，返回PURPOSE_NOT_EXECUTABLE；此限制不因有效人工receipt放宽。

模型工具输入schema采用object/properties/required/enum/type等基础子集，避免强制客户端支持if/dependentRequired；租约成对、动作条件和状态相关校验在服务端严格执行。契约文件的status、semantic_constraints_not_wire_schema是设计元数据，不作为MCP Tool字段发送。
