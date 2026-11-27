# OMB-003D F-02 实机审批平台

裁决 `BLOCKED_APPROVAL_PLATFORM`。此次验证限定在本机原生诊断。候选业务版本仍为 0.3.0b9。

## 当前证据

| 项目 | 结果 |
| --- | --- |
| 宿主 | macOS 26.6.2、arm64、Aqua，当前执行用户与控制台用户一致 |
| 工具 | Apple Swift 6.3.2，检测到 OpenMausBot 0.1.184 |
| 签名身份 | 本次查询找到 0 个有效代码签名身份 |
| Secure Enclave | Native CryptoKit 在当前执行会话报告不可用 |
| 认证策略 | 设备所有者认证及生物认证均返回 `NSCocoaErrorDomain 4099` |
| 人工在场 ACL | `privateKeyUsage` 和 `userPresence` 结构创建成功 |
| 实际硬件签名、无交互拒签和人工取消 | `PENDING` |
| 可信签名组件、独立控制通道和公钥登记 | `PENDING` |

ACL 创建结果只证明系统接受了访问控制描述。当前执行会话的能力读数无法判断操作者图形会话中的签名结果。候选服务继续保持审批锁定。

## 操作者会话诊断

在 MacBook 已登录的图形会话中，从本机 Terminal 使用：

```sh
/bin/sh scripts/run_approval_presence_probe.sh --interactive
```

诊断编译到临时目录。硬件可用时，诊断仅使用固定测试消息，尝试两次独立的系统在场确认，并要求在最后一次认证对话框中选择取消。每次认证使用新的 LocalAuthentication 上下文。诊断还会在交互测试前后验证禁止交互的调用应当拒绝签名。密钥的加密表示只驻留诊断进程内存。输出仅含检查状态和系统错误码。[Apple Secure Enclave P‑256 签名密钥](https://developer.apple.com/documentation/cryptokit/secureenclave/p256/signing/privatekey)、[Apple LocalAuthentication 上下文](https://developer.apple.com/documentation/localauthentication/lacontext?changes=_3&language=objc)

即使诊断报告 `PRIMITIVES_PASS`，F-02 仍须核验实际审批组件的可信代码签名、控制通道对端身份和公钥登记完整性。现场记录还需确认分别出现两次真实系统认证提示，以及取消产生的实际结果。[003A 审批合同](../design/omb003a/HUMAN_REVIEW_APPROVAL.md)
