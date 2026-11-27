# F-02 MCP 实机登记副本验收

在 MacBook 上使用本机 MCP SDK 通过真实 stdio 连接开发服务。第一次启动与关闭后第二次启动各建立独立服务进程。隔离 D5 副本保留了原生 Secure Enclave 实测登记中的未激活候选和原有只读 Bot 绑定。

| 检查 | 结果 |
| --- | --- |
| 初始化和工具发现 | 两次均成功，均发现 9 项开发工具 |
| 查询和错误返回 | 两次查询列表成功。未知任务返回 `NOT_FOUND_OR_FORBIDDEN`，无效分页参数返回 `INVALID_ARGUMENT` |
| Bot 权限 | 未知绑定启动被拒绝。原只读绑定创建草稿被拒绝 |
| 审批接口隔离 | 审批、挑战和签名收据工具均未公开。直接调用均被拒绝 |
| 运行状态 | 协调器未启动时拒绝连接，两次正常运行使用不同启动标记。原候选仍未激活，任务、事件、审批挑战和决定均为零 |
| 独立可写副本 | 另一个由 D4 迁移的合成测试副本通过四次协议版本协商及草稿创建、幂等重试、拒绝外加审批字段、任务和事件查询 |
| 完整性及回归 | 两个测试的源数据库 SHA-256 在测试前后一致。全量回归 316/316 通过 |

本轮覆盖 MCP SDK 和本机开发 stdio。OpenMausBot 和 Magpie 应用内联调未在本轮执行。正式签名 XPC 仍为 `BLOCKED_APPROVAL_PLATFORM`，003E 至 003G 保持 `HOLD`。

## 复现

在本仓库运行以下命令。参数为原实机登记会话目录及对应的证据包。脚本将在 `.devdata` 下创建一次性副本。

```sh
PYTHONPATH=src:frozen_payload/source/src .venv/bin/python scripts/check_enrollment_mcp.py \
  "$HARDWARE_SESSION_DIR" "$HARDWARE_EVIDENCE_ZIP"
```
