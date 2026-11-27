# OMB-003D 审核门控与 MCP

`MCP_AND_REVIEW_REQUEST_VERIFIED / BLOCKED_APPROVAL_PLATFORM`。基础代码可审查，完整 003D 准入仍待人工在场签名及可信控制面验证。

| 项目 | 结果 |
|---|---|
| 回归 | 189 项通过，含 14 项本阶段新增、17 项 003C、126 项延续的 003B、32 项冻结历史用例 |
| 新版 MCP | 本机真实 stdio 工具发现 9 项。官方客户端验证创建、重复请求、拒绝 `approved`、读取任务和事件。新服务名为 `aars-task-dev` |
| 协议 | 实测 `2024-11-05`、`2025-06-18`、`2025-11-25` 分别协商到相同版本。对探测值 `2099-01-01`，服务回报 `2025-11-25`，兼容性由客户端决策 |
| 审核申请 | 仅在本机合成验证任务拥有有效租约和可用证据时接收。申请、租约提交、任务版本、审核事件、幂等结果同事务提交 |
| 审核失效 | 过期、策略或绑定变化、证据撤销及重启后可追溯。读时和重放会重新判断有效性，协调器扫描、撤销或重启时将失效审核和暂停记录提交 |
| 审批平台 | `BLOCKED`。当前非交互探测报告 Secure Enclave 不可用、本地生物认证策略不可用及 0 个有效签名身份。ACL 结构可以构造，逐次在场签名、隔离的控制通道及可信公钥登记尚未验证 |
| 开发库升级 | C2 离线备份复制到独立 D3 库，原库 SHA256 一致。冻结 OMB-002-FIX 源码和实机配置保留 |

服务启动器在本机私有开发目录读取预先配置的 Bot 绑定，只附着到已持有运行锁的协调器。工具请求不携带身份、路径、私钥、原始挑战或签名收据。MCP 工具注释用于展示，服务端按参数和业务规则校验。MCP 工具定义来自已评审契约，返回 JSON 放在文本内容中。依据 [MCP 工具规范](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)。

结果申请锁定任务版本、定义指纹、证据集合、绑定和策略上下文，并将承诺值写入原有事件链。此阶段的 `nonce_hash` 是合同要求的保留字段，随机原像已丢弃。未来经过验证的审批组件须生成独立且一次性的真实挑战。待审窗口最长 120 秒，证据先到期时以其时间为限。应用仍需可信运行协调器定期调用恢复扫描。新 `review.request` 能力需显式配置，迁移会保留旧绑定能力。

人工批准、开工和续租许可返回锁定错误。现有条件不能证明签名操作由人工逐次授权，也不能证明公钥设置受可信组件保护。探测仅验证执行上下文中的可用性。Apple 的接口要求见 [Secure Enclave 密钥说明](https://developer.apple.com/documentation/security/protecting-keys-with-the-secure-enclave.md)及 [userPresence](https://developer.apple.com/documentation/security/secaccesscontrolcreateflags/userpresence)。

## 重现与回滚

- 回归入口 `.venv/bin/python scripts/run_tests.py --scope full`。独立 Python 3.13 环境保留父版本依赖，MacBook 实机 Bot 验收仍在 OMB-003F。
- 测试入口 `PYTHONPATH=src:frozen_payload/source/src .venv/bin/python scripts/mcp_smoke.py <已停止的C2开发库路径>`。脚本以私有副本验证开发 MCP 入口、协议、EOF 与原库指纹。
- 实际 MCP 进程入口 `python -m aars_task_manager.mcp_server --data-root <本仓库.devdata下的私有目录> --binding-id <可信宿主绑定>`。需要独立协调器已运行，部署集成后由宿主负责其生命周期。
- D3 只通过离线副本迁移。停用 D3 开发进程后可继续使用原 C2 库。保留 D3 文件、事件和测试记录供复核。

后续阶段根据各自授权推进。完成 003D 验收需要可部署的可信签名组件、受保护的公钥登记以及真实在场、取消、无人值守拒绝和重放等验证。
