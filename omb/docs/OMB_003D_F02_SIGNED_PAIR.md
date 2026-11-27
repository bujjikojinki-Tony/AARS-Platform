# F-02 正式签名组件双向连接验收

2026-11-27 在 MacBook 上编译了隔离诊断程序并执行了原生签名检查。可信签名组件连接为 `BLOCKED`，审批平台裁决为 `BLOCKED_APPROVAL_PLATFORM`。

## 实测结果

| 检查 | 结果 | 观测 |
| --- | --- | --- |
| Swift 诊断编译 | PASS | 本机 macOS 26.6.2 |
| 无可用身份时停止构建 | PASS | 代码签名身份库存为 0。选择未安装的指纹，构建退出码 2，目的应用未生成 |
| 临时签名的宿主和服务 | PASS | 以匹配的 Team ID 写入签名覆盖范围内的配置，静态身份检查仍拒绝两个组件，系统返回 `-67050` |
| 配置缺失或与预期不符 | PASS | 分别返回 `missing_team_configuration` 与 `expected_team_mismatch` |
| 正式签名的双向 XPC 正向连接 | BLOCKED | 本机无可用代码签名身份 |
| 全量回归与冻结输入 | PASS | 316/316 项测试通过，四项冻结输入 SHA-256 一致 |

宿主和服务分别验证对端的 Apple 签名链、限定角色标识及 Team ID，签名要求在 XPC 连接启用前设置。服务同时核对连接的有效用户 ID。双方仅交换本机服务进程号。诊断程序的成功报告仍单独保存审批平台的 `BLOCKED_APPROVAL_PLATFORM` 裁决。使用的系统机制见 [Apple NSXPCConnection](https://developer.apple.com/documentation/foundation/nsxpcconnection/setcodesigningrequirement%28_%3A%29) 和 [Apple 代码签名要求技术说明](https://developer.apple.com/documentation/technotes/tn3127-inside-code-signing-requirements/)。

## 正向验收复现

在本机授权的签名身份可用后，使用独立确认的 Team ID 和本地钥匙串中对应的身份指纹构建诊断应用。`--inventory` 仅报告有效身份数量。构建器先签内嵌服务，再签宿主，随后执行包完整性和各组件的 Apple 签名、角色及 Team ID 检查。

```sh
python3 scripts/build_signed_approval_probe.py --inventory
python3 scripts/build_signed_approval_probe.py \
  --identity "$SIGNING_FINGERPRINT" \
  --team-id "$EXPECTED_TEAM_ID" \
  --destination "$ISOLATED_DIAGNOSTICS_DIR/F02SignedPair.app"
open "$ISOLATED_DIAGNOSTICS_DIR/F02SignedPair.app"
```

在 Mac 桌面会话打开应用后保留同目录的 `F02_SIGNED_PAIR_*.json`。正向通过要求报告 `SIGNED_XPC_PASS` 和两个不同的实际进程 ID。独立信任配置下的生产公钥登记及激活仍有各自的验收要求。003E 至 003G 保持 `HOLD`。
