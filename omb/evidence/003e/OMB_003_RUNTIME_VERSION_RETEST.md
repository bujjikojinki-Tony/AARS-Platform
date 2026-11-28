# OMB-003 MacBook 运行版本复核

TM-MAC-01 为 `VERSION_DRIFT_RETEST_REQUIRED`。升级影响项是 OpenMausBot 调用新版 Magpie 的应用内验收。

| 组件 | 本轮实测 | 依据 |
|---|---|---|
| OpenMausBot | 0.1.184 | 已安装应用的版本与既有预检一致，回环服务进程映射到该应用包。 |
| Magpie | 0.1.4971 | 已安装应用包和其本机可执行文件的版本输出一致。此前应用内联调使用 0.1.4936。 |
| Python | 3.13.7 | 003 启动器所指工作树虚拟环境。 |
| MCP SDK | 2.3.0 | 003 虚拟环境安装元数据，与锁文件一致。 |
| SQLite | 3.50.4 | 同一 Python 进程报告的实际 SQLite 运行库版本。 |

开发锁文件的 35 项版本逐一匹配。重跑 MCP 适配器、监督进程及协议边界测试，21/21 通过。这些测试覆盖当前 Python/MCP 环境。新版 Magpie 在 OpenMausBot 内的真实工具调用尚待补验，TM-MAC-03 仍为 `PARTIAL`。

本机有效 Apple 签名身份为 0，正式在场审批仍受阻。OMB-003 总裁决为 `BLOCKED`。
