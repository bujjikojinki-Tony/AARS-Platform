# 组件分工与未来阶段边界

所有模块名/方法名均为未来设计，当前未创建代码或分支。

|组件|未来位置|职责|禁止承担|阶段|
|---|---|---|---|---|
|TaskAggregate|aars_task_manager/domain|apply(command, trusted_context, expected_version)；状态机、用途和版本不变量|网络/模型调用、直接批准|003B|
|TaskRepository|aars_task_manager/storage|单连接事务、CAS、Revision、Event及幂等同提交，显式关闭|写入002DB，跨库原子性声明|003B|
|TaskApplicationService|aars_task_manager/service|身份/授权、命令编排、限制/错误映射|采信工具入参中的身份、执行任意shell|003B|
|RecoveryCoordinator|aars_task_manager/recovery|完整性、boot租约与challenge失效、明确恢复事件|自动完成、自动批准或重跑生产动作|003B/C|
|CoreEvidenceAdapter|aars_task_manager/evidence|调用冻结SDK/序列化验证闭包、登记不可变快照、用途核查|修改Core枚举/默认状态、伪造来源/许可|003C|
|EventProjectionAdapter|aars_task_manager/events|读取已提交事件、重建投影；外发如有必须另审outbox|把外部投递声称为同库事务的一部分|003C|
|McpTaskAdapter|独立003 stdio服务器|仅9个新工具、基础schema、严格语义校验、稳定响应|给002原服务器加功能、暴露approve|003D|
|ApprovalBroker + trusted UI|独立本机签名组件|逐次在场认证、只签锁定挑战、保护P-256私钥|共享secret/普通CLI自动批准|003D平台门|
|OperatorControlAdapter|独立本机控制通道|peer/公钥完整性、challenge/receipt、人工决策事务|复用/提取OpenMausBot桌面令牌|003D|
|AcceptanceHarness|独立测试目录|32历史+80新增；原请求/结果/turn/版本/截图归档|用模型改写或模拟结果替代实机|003E/F|

003B前提仍是补齐来源处置与操作者新批准。即使未来003B获准，也只实现管理聚合与独立库，不自动解锁003C～G；在审批broker未验证前，所有人工许可动作fail closed。单元测试可使用明确的受控fixture建立前置状态，但不能把fixture签名或测试stub算作真实人工审批，不能把这些fixture部署到运行服务。

定义共享原则：状态允许集、错误码、ID/字段限制及版本规则应在未来同一契约模块引用，MCP/控制面/存储不可各写一套授权逻辑。写操作最终经过同一聚合服务和仓储事务；单独handler无法绕过相同guard。锁不跨模型等待或人工交互持有。
