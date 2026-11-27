# WP-09 新增测试矩阵

**80项新增用例已定义，0项执行；状态全部PLANNED_NOT_EXECUTED。** 本轮只有旧32项实际执行通过，不把设计检查计入新增功能测试。每项mandatory=true。

原始结构化矩阵见TEST_MATRIX.json，包含前置条件、步骤、预期、环境与未来阶段。UNIT不替代MAC_REQUIRED；环境不足记BLOCKED，不用mock替代人工在场和实机工具调用。

## MODEL — WP-02 / 003B / UNIT

|ID|用例|前置条件|动作|通过判据|
|---|---|---|---|---|
|TM-MODEL-01|完整Task创建|合法定义与绑定|创建并读取Task|ID服务生成、version=1、state=DRAFT、definition_hash可复算|
|TM-MODEL-02|Task与Core类型隔离|加载冻结Core ObjectType|检查Task持久化与SDK调用|Core原9类型不变，Task不伪装Observation/Evidence|
|TM-MODEL-03|定义版本规则|DRAFT version=3 definition_revision=1|修改title|version=4、definition_revision=2，旧Revision保留|
|TM-MODEL-04|状态与定义版本分离|READY、已批准定义|start并续租|version递增，definition_revision和hash不变|
|TM-MODEL-05|严格数据类型|布尔version、空白title、超长说明|逐一发请求|INVALID_ARGUMENT，无Task或事件写入|
|TM-MODEL-06|时间与精度|时区缺失、due_at过期、NaN|校验输入|无时区/NaN拒绝，合法过期due只标逾期不自动执行|
|TM-MODEL-07|ID不复用与终态|存在终态Task|尝试重开/重用ID|拒绝；后继任务新ID且supersedes可追溯|
|TM-MODEL-08|无变化更新|DRAFT原title|新幂等键提交相同title|NO_CHANGE，version和event数不变|

## STATE — WP-03 / 003B / UNIT

|ID|用例|前置条件|动作|通过判据|
|---|---|---|---|---|
|TM-STATE-01|全部允许转换|覆盖19条允许边并满足各guard|逐条执行|仅目标状态/版本/事件按契约变更|
|TM-STATE-02|未列出转换穷举|所有state×action组合减允许集|逐一尝试|默认拒绝，零状态变更|
|TM-STATE-03|终态不可写|4种终态|update/start/link/review等|除明确usage失效审计外均拒绝|
|TM-STATE-04|缺前置条件|READY但无计划许可/范围不符|start|拒绝，无attempt创建|
|TM-STATE-05|未经审核不能完成|RUNNING有效租约|伪造complete或目标COMPLETED|未知动作/字段拒绝，不完成|
|TM-STATE-06|审核证据不足|RUNNING零可用Evidence|request_review|EVIDENCE_UNUSABLE，保持RUNNING|
|TM-STATE-07|人工要求修改|有效RESULT review和在场receipt|request_changes|READY，review关闭，下一次attempt不同|
|TM-STATE-08|逾期租约恢复|RUNNING lease过期|恢复扫描及迟到写入|PAUSED、旧attempt EXPIRED；迟到写入拒绝|

## CONCUR — WP-05 / 003B / SQLITE_PROCESS

|ID|用例|前置条件|动作|通过判据|
|---|---|---|---|---|
|TM-CONCUR-01|相同版本竞争|两连接同version|并发update|仅1次提交，另一VERSION_CONFLICT；事件只增1|
|TM-CONCUR-02|多Bot启动竞争|操作者明确授权两worker、同READY版本|两个进程同时start|仅1活动attempt，另一冲突，无双租约|
|TM-CONCUR-03|同键同请求并发|相同principal/key/hash|24次并发create|仅1Task和首事件，其余回放相同ID|
|TM-CONCUR-04|同键异请求|同principal/key不同title或method|并发提交|一项成功，另一IDEMPOTENCY_CONFLICT|
|TM-CONCUR-05|提交后响应丢失|服务已COMMIT、断开stdio|原key重连重试|返回原结果，version不再增，不重复副作用|
|TM-CONCUR-06|锁忙有界重试|外部连接持写锁|调用变更|5秒总界内DB_BUSY；释放后原key可安全重试|
|TM-CONCUR-07|旧fencing隔离|旧attempt过期，新attempt已创建|旧Bot携旧token提交|FENCING_CONFLICT，无新attempt污染|
|TM-CONCUR-08|授权与幂等竞态|请求成功后撤销绑定|原key回放及在事务中撤销|拒绝新访问，不能借缓存泄露或再次写入|

## DB — WP-05 / 003B / SQLITE_PROCESS

|ID|用例|前置条件|动作|通过判据|
|---|---|---|---|---|
|TM-DB-01|路径隔离|传入002路径/符号硬链接/同inode|启动003|拒绝，002文件hash不变|
|TM-DB-02|权限与连接释放|开发库0700/0600|循环请求并检查句柄/锁|无连接泄漏，私有权限保持|
|TM-DB-03|事务中断|在Task更新后event/revision写入前注入异常|提交失败再查询|全部回滚，无半状态或孤立幂等记录|
|TM-DB-04|数据库实例识别|未知application_id或较新user_version|启动旧程序|拒绝写入，不自动迁移|
|TM-DB-05|重启恢复|RUNNING任务+活动lease|终止进程再启动|PAUSED且旧boot租约无效，已提交数据保留|
|TM-DB-06|未提交崩溃|事务未COMMIT时进程终止|重新打开|无半任务/半事件，integrity_check通过|
|TM-DB-07|哈希/事件链篡改|改object bytes、跳event seq|启动/读任务|INTEGRITY_FAILURE并隔离，不自动修复通过|
|TM-DB-08|日志模式门|SQLite3.50.4、尝试开启WAL|启动预检|默认DELETE；未修补版本WAL拒绝|

## AUTH — WP-06 / 003D / MCP_PROCESS

|ID|用例|前置条件|动作|通过判据|
|---|---|---|---|---|
|TM-AUTH-01|缺失启动绑定|无binding或未知binding|initialize后调用Task工具|拒绝，不默认admin|
|TM-AUTH-02|参数身份伪造|Bot提交actor_id=operator/clientInfo自称human|调用受控动作|未知字段或权限拒绝，身份不提升|
|TM-AUTH-03|跨Task越权|Bot A无B任务ACL|get/list/events/update|不泄露B存在性，无变更|
|TM-AUTH-04|跨workspace隔离|相同id/key不同workspace|查询与变更|只作用已绑定workspace，无跨域FK引用|
|TM-AUTH-05|绑定撤销|已有lease/review|操作者撤销binding|新请求拒绝，lease无效、review STALE|
|TM-AUTH-06|工具投放范围|独立003测试Bot|查所有Bot MCP列表|只分配Bot可见；002服务器配置不改|
|TM-AUTH-07|普通CLI不能批准|同用户Bot可执行普通CLI/写批准JSON|尝试生成批准|无在场签名即拒绝，Task不完成|
|TM-AUTH-08|默认单操作者|多Bot或公网配置未获准|尝试启动/扩scope|fail closed，不自动创建管理员/公网监听|

## EVID — WP-07 / 003C / UNIT_SQLITE

|ID|用例|前置条件|动作|通过判据|
|---|---|---|---|---|
|TM-EVID-01|固定fixture关联|已验证002合成快照与父Observation|登记并链接|USABLE_FIXTURE、hash可复算、无新观测值|
|TM-EVID-02|Observation不自动成为Evidence|仅Observation快照|link|拒绝类型，不能进入证据集合|
|TM-EVID-03|Core图不完整|Evidence缺父Observation|登记快照|SDK认证不通过，不能标可用|
|TM-EVID-04|来源hash不可用|provenance sha256:unavailable|尝试标真实来源已验证|拒绝真实等级；fixture须明确标注来源限制|
|TM-EVID-05|目录PENDING隔离|候选目录元数据|进入研究Evidence链|拒绝，不修改目录授权状态|
|TM-EVID-06|同ID不同内容|已存在snapshot A|登记变更内容为A同ID|新digest+显式supersedes；A不可覆盖|
|TM-EVID-07|许可失效追溯|REVIEW_PENDING或COMPLETED关联|撤销/过期来源用途许可|待审STALE；已完成usage需复核；历史不删除|
|TM-EVID-08|证据集合竞态|review准备后link版本变化|提交旧receipt|REVIEW_STALE，不能批准新集合|

## APPROVAL — WP-08 / 003D / MAC_REQUIRED

|ID|用例|前置条件|动作|通过判据|
|---|---|---|---|---|
|TM-APPROVAL-01|人工批准计划/结果|可信界面、有效当前review|逐次在场签名并提交|READY/COMPLETED正确变化，receipt可验|
|TM-APPROVAL-02|Bot直接批准|Bot可见全部MCP工具|搜索/调用approve或approved=true|无入口/字段拒绝，不生成ApprovalDecision|
|TM-APPROVAL-03|伪造签名或公钥|Bot构造receipt/替换公钥登记|提交控制面|签名/登记完整性门拒绝|
|TM-APPROVAL-04|nonce重放|已消费有效receipt|再次提交或换任务/DB实例|只回放原决定或拒绝，零新批准|
|TM-APPROVAL-05|签名后改版本|receipt准备后Task/policy/binding变化|提交receipt|STALE，不自动更新签名内容|
|TM-APPROVAL-06|认证取消或无交互|触发认证后取消/从Bot无人值守调用|请求签名|无签名与批准，无密码/生物信息入日志|
|TM-APPROVAL-07|每次人工在场|刚批准一项、认证上下文尚热|紧接着批准另一项|每项仍需新在场，不能复用缓存|
|TM-APPROVAL-08|硬件/桥接不可用|无Secure Enclave/Keychain或签名helper失败|尝试批准|LOCKED/BLOCKED，不退化普通CLI/软件token|

## MCP — WP-04 / 003E / MCP_PROCESS

|ID|用例|前置条件|动作|通过判据|
|---|---|---|---|---|
|TM-MCP-01|旧五工具兼容|002冻结版本与003侧适配|比对名称schema及旧32回归|旧接口语义不变，003不替换002服务器|
|TM-MCP-02|真实生命周期|官方客户端与OpenMausBot|initialize/initialized/list/call/EOF|正确协商、关闭，无stdout杂音|
|TM-MCP-03|协议版本矩阵|2024/2025协议与未知版本|连接各测试客户端|协商值有原始记录，不支持版本明确拒绝|
|TM-MCP-04|输入边界|未知字段/过大请求/非法ID/布尔版本|原样协议请求|服务端拒绝，不靠模型改写参数算通过|
|TM-MCP-05|分页完整性|超50任务/事件、16KiB边界|逐页读取并篡改cursor|不丢/不重、显式next；篡改/过期拒绝|
|TM-MCP-06|业务错误封装|版本冲突/非法转换|实际调用|isError=true、稳定code、无SQL/路径/堆栈泄露|
|TM-MCP-07|幂等与request id区别|相同幂等键不同JSON-RPC id|重连重试|只回放一次结果；request id不充当幂等键|
|TM-MCP-08|输出与注入隔离|Evidence/标题含Markdown与指令文本|查询并在UI显示|作为不可信文本，无HTML执行/系统指令采纳|

## MAC — WP-09 / 003F / MAC_REQUIRED

|ID|用例|前置条件|动作|通过判据|
|---|---|---|---|---|
|TM-MAC-01|真实版本记录|安装的四组件及SQLite|启动前采集实际版本|版本/绝对路径/依赖锁一致，差异触发重测|
|TM-MAC-02|GUI环境启动|从Finder启动OpenMausBot|连接独立003MCP|不依赖终端PATH，能发现约定工具|
|TM-MAC-03|Magpie真实调用|操作者选择Magpie专用测试Bot|创建/查询/变更/请求审核|turn ID对应实际Magpie，无静默fallback记通过|
|TM-MAC-04|实际应用重启|已有任务/事件/Evidence|退出重开应用并再次查询|PID改变，数据不丢、旧租约不复用|
|TM-MAC-05|并发实机冲突|两个明确授权测试绑定|同时修改同Task版本|冲突明确，仅一次提交，无状态覆盖|
|TM-MAC-06|真实人工在场门|实际Mac可信界面|批准/拒绝/取消认证|对应结果和签名日志齐全；Bot不能自批|
|TM-MAC-07|本地网络边界|运行003及002|检查监听与非法访问|无非预期公网服务，未授权调用拒绝|
|TM-MAC-08|原有应用回归|002与其他Bot原工作流|执行原工具查询及用户常用操作|原功能正常；实际证据与用户确认分开|

## RELEASE — WP-10 / 003G / MAC_REQUIRED

|ID|用例|前置条件|动作|通过判据|
|---|---|---|---|---|
|TM-RELEASE-01|源码Commit绑定|独立003分支与原冻结输入|比对Git Commit与完整Manifest|Commit真实存在、逐文件可验证；不补造历史|
|TM-RELEASE-02|包完整与敏感信息|候选发布ZIP|校验条目/hash/secret模式|清单完整，无凭证/无关聊天/虚拟环境|
|TM-RELEASE-03|迁移失败回滚|独立003库一致备份|在副本迁移中断|原003备份可恢复，002hash不变|
|TM-RELEASE-04|旧二进制回滚|新schema已写数据|切回旧二进制+旧备份|旧schema可读，新事件先归档且时间点明确|
|TM-RELEASE-05|003停用回002|003运行出现缺陷|停用003并使用002原launcher|002健康/9对象完整，003历史不删除|
|TM-RELEASE-06|缺证据默认不通过|缺截图/原始日志/实机门结果|执行发布评审|PENDING/BLOCKED，不能BASELINE_FREEZE_PASS|
|TM-RELEASE-07|授权阶段门|仍仅003A授权|请求实现/部署/冻结动作|003B～G HOLD，无自动推进|
|TM-RELEASE-08|最终全部门|80新增+32历史+实机+人工批准|审查完整验收包|仅全部具证通过才允许新冻结|

