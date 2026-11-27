# WP-06 本机单操作者与Bot身份

威胁边界保持002：操作者控制MacBook，Bot通过明确分配的本地MCP能力访问任务；不提供公网、多租户或对恶意同UID进程的强隔离承诺。但必须在该边界内阻止Bot通过接口自行提升权限或批准任务。

可信身份来自操作者建立的PrincipalBinding与专用stdio启动器。绑定文件位于非Bot任务目录的私有配置路径，含binding_id、host_bot_id、workspace_id、capabilities、binding_version；服务启动解析并固定上下文。工具参数、任务标题、MCP clientInfo.name、模型自称operator均不采信。未知/缺失/已撤销绑定拒绝调用，不使用默认管理员。OpenMausBot server.bot范围只是第一层投放控制，服务端仍核查任务ACL和用途。

同一UID可以读取普通0600配置，因此该绑定仅是可信本机启动上下文，不是密码学Bot身份。不同Bot若可任意启动同用户程序，可能复用该启动器；不得宣称靠环境变量或文件权限已经解决恶意Bot冒充。默认只给一个003测试Bot；多Bot用例在操作者明确建立第二个绑定后的隔离开发库执行。人工批准还必须依赖下述单独在场认证，不依靠这一弱绑定。

|主体|允许|拒绝|
|---|---|---|
|owner Bot|在已分配scope创建DRAFT、读自己任务、DRAFT白名单编辑、持当前租约工作/关联已有合成Evidence、请求审核|批准/拒绝、改绑定/策略、改owner、任意state、执行生产动作、导入真实数据或任意文件|
|协作Bot|只有操作者显式配置的任务级read/propose/worker能力|从任务ID推断权限、跨workspace查询、替owner写入、过期attempt写入|
|OPERATOR|经可信控制面和逐决定在场认证批准计划/结果、拒绝/要求修改、取消、退回、恢复、调整绑定|通过自然语言或MCP布尔值替代认证；批量授权所有数据资源|
|SERVICE|完整性核查、租约失效恢复、来源/许可失效标记|自动批准、自动重跑导致外部副作用、静默删除|

授权顺序：绑定有效→workspace范围→Task ACL→purpose/数据准入→操作角色→状态/版本→租约/审核约束。每个写事务重查，不能只在tools/list或首次initialize检查。绑定撤销使新请求和幂等回放都拒绝，活动租约失效，待审核STALE；COMPLETED历史保留，usage_state重新评估。

控制面不复用或提取OpenMausBot内部桌面令牌，不弱化其403保护。审批界面/Keychain helper为003D前必须验证的独立能力，未实现时所有operator决定fail closed。普通CLI、可写JSON文件或`approved=true`都不能充当可信人工批准。

数据最小化：日志保留request/turn/binding标识、原参数digest和实际结果；不记模型密钥、用户密码、审批认证材料或生物信息。自由文本、模型结果、Markdown和Evidence解释均为不可信内容；UI以纯文本/安全渲染展示，不能作为系统指令或shell命令执行。
