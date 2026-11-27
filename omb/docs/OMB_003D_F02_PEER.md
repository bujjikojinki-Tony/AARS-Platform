# F-02 本机审批对端身份诊断

候选业务版本为 b9。审批裁决仍为 `BLOCKED_APPROVAL_PLATFORM`。

`ApprovalPeerIdentity` 用配置中的 Apple Team ID 和固定角色标识编译签名要求。静态检查验证组件签名与封装资源。运行时监听器在激活前限制审批组件身份，连接在首条消息前限制服务身份。测试协议只返回诊断用进程号。[Apple 代码签名要求](https://developer.apple.com/documentation/technotes/tn3127-inside-code-signing-requirements/)、[Apple XPC 监听器签名要求](https://developer.apple.com/documentation/foundation/nsxpclistener/setconnectioncodesigningrequirement%28_%3A%29)、[Apple XPC 连接身份](https://developer.apple.com/documentation/Foundation/NSXPCConnection)

- 9 项静态用例通过，覆盖临时签名、参数与路径校验以及签名后变更的封装。
- 同进程匿名 XPC 上的无业务探测正常返回。启用监听器身份校验后，临时签名客户连接在进入委托前被拒绝。启用客户端身份校验后，临时签名服务被系统拒绝，返回 4102。
- 独立进程测试使用内嵌诊断服务。命令行启动返回 4099，桌面启动未生成报告。这两项尝试尚未给出独立进程结论。
- 当前会话有 0 个有效代码签名身份。真实受信任组件连接、公钥登记及生产审批仍待验收。业务回归 298 项通过。
