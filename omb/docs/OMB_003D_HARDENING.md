# OMB-003D 本机协议加固与审批平台复查

`LOCAL_MCP_VERIFIED / BLOCKED_APPROVAL_PLATFORM`。开发版本 `0.3.0b4`，基于 `62fe34d851c1c3ce44b64149cccf3c3fa2dbefff`。

| 项目 | 实际结果 |
|---|---|
| MCP 读取限制 | 在 SDK 解析前，每个 UTF-8 帧最多读取 64 KiB（含换行）。超限、无效 UTF-8 和缺少换行的帧结束该会话。CLI 返回退出码 2，标准错误仅输出固定错误码 |
| 正常协议 | 边界长度帧可协商。通过真实 CLI 重跑三种受支持协议和一个未知版本的协商测试。工具参数的 16 KiB 业务限制继续执行 |
| 证据撤销 | 官方 MCP 客户端经真实本地 stdio 进程关联证据、提交审核。测试宿主撤销合成夹具后，重放返回 `REVIEW_STALE`，读取显示任务已暂停。测试租约明确标注 |
| 历史与新增回归 | 194 项通过，0 失败，0 跳过。包括 5 项本轮新增和 32 项冻结部署历史用例 |
| 开发库复制 | 以实际 C2 开发库复制 D3 副本，验证正常 MCP 流程，原库 SHA256 相同 |
| F-02 | 当前执行环境返回 Secure Enclave 不可用，设备所有者认证和生物认证能力查询均返回 NSCocoaErrorDomain 4099。检测到 0 个有效代码签名身份 |

最外层 64 KiB 是传输预算，允许 JSON 转义及 JSON-RPC 信封。SDK 仍处理帧解码后的协议协商、消息验证和输出。标准输入描述符在会话期间指向空设备，业务代码不会从同一管道取数据。D3 数据库结构和已经评审的工具协议保持兼容。

平台检查范围仅是当前非交互进程。可以构造 `userPresence` ACL，并没有因此得到逐次人工在场签名。F-02 解锁需要在交互式 macOS 会话验证受信任、签名可核实的审批组件，以及受保护的公钥登记、人工确认、取消和重放拒绝。审批、开工和续租权限保持锁定。003E～003G 继续处于既定阶段门。

回归命令为 `.venv/bin/python scripts/run_tests.py --scope full`。复查脚本 `scripts/check_approval_platform.swift` 仅读取能力并构造内存中的 ACL。`APPROVAL_PLATFORM_RECHECK.json` 记录此次观察值，`MCP_DEV_RUNTIME_EVIDENCE.json` 记录实际协议和工具响应，JUnit 记录全部回归用例。
