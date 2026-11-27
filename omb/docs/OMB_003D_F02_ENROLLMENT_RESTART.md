# F-02 实机登记的崩溃恢复复验

复用 MacBook 原生诊断保存的 Secure Enclave 登记证明和隔离 D5 数据库。五份原始 JSON 与前次证据包清单中的 SHA-256 一致，P-256 历史签名复验通过。启动、拒绝测试及重启全部在一次性数据库副本上执行。

| 检查 | 裁决 | 实测结果 |
| --- | --- | --- |
| 异常退出与恢复 | PASS | 第一个进程以诊断退出码 73 退出。第二个进程判定旧运行标记失效，启动新会话并在正常关闭时清除运行标记 |
| 候选公钥与数据库完整性 | PASS | D5 完整性检查通过。原候选公钥仍未激活，任务、事件、审批挑战及决定均为零 |
| 重放登记证明 | PASS | `APPROVAL_ENROLLMENT_CHALLENGE_MISSING` |
| 再次申请登记 | PASS | `APPROVAL_ENROLLMENT_EXISTS` |
| 用未激活候选申请审批挑战 | PASS | `APPROVAL_KEY_UNTRUSTED` |
| 源数据库完整性 | PASS | 测试前后 SHA-256 一致 |

审批平台裁决为 `BLOCKED_APPROVAL_PLATFORM`。验收覆盖隔离 D5 副本与原始实机证明。正式签名双向 XPC 及可信公钥激活仍待验收，003E 至 003G 保持 `HOLD`。

## 复现

在本仓库运行以下命令。第一个参数是此前实机登记会话目录，第二个参数是该会话对应的证据包。

```sh
PYTHONPATH=src:frozen_payload/source/src .venv/bin/python scripts/check_enrollment_restart.py \
  "$HARDWARE_SESSION_DIR" "$HARDWARE_EVIDENCE_ZIP"
```
