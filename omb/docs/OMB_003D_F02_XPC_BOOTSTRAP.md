# F-02 独立进程 XPC 桌面验证

桌面测试在真实 Mac 会话中完成。宿主进程与内嵌 XPC 服务进程独立运行。候选业务版为 b9，人工审批平台继续为 `BLOCKED_APPROVAL_PLATFORM`。

## 本轮变更

对齐内嵌服务的 Bundle ID、代码签名标识和连接名称。分开记录服务握手、诊断端点、拒绝结果和受保护监听器接入计数。各握手单独处理拒绝或超时。诊断消息限于探测及其状态。[Apple 内嵌 XPC 服务](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingXPCServices.html)、[Apple XPC 监听器端点](https://developer.apple.com/documentation/foundation/nsxpclistenerendpoint?changes=_5_2)

## 实测

- 桌面宿主 PID 30548，内嵌服务 PID 30572。最小握手与普通探测均由同一个服务进程返回。
- 加入签名要求后，服务监听器拒绝临时签名的客户端，受保护委托接入计数为 0。客户端拒绝临时签名的服务，返回系统代码签名要求错误 4102。第二个方向以系统错误及探测无回复为证。原始报告中的占位计数已从后续诊断输出去除。
- 命令行会话仍在最小握手前返回 4099。这一会话的结果独立保留。桌面运行提供跨进程拒绝实证，现阶段无法单独归因早期启动失败。
- 同进程 XPC 测试重新通过。Python 业务回归 298/298 通过，四项冻结输入指纹匹配。

授权组件的有效签名、可信公钥登记，以及两端都具备真实授权签名的连接验收仍待完成。临时签名仅用于隔离诊断。
