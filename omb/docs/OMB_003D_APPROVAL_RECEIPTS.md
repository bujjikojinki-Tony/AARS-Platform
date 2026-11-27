# OMB-003D 审批收据验证候选

开发版本 `0.3.0b5`。结果审核收据验证与本机互操作测试通过。人工在场审批继续处于 `BLOCKED_APPROVAL_PLATFORM`。

- `approval_receipts.py` 从已核验的审核历史读取当前待审结果，绑定工作区、数据库实例、任务和审核 ID、任务版本、定义与证据指纹、策略、绑定版本及授权范围。只支持已有的本机合成结果审核。
- 校验器使用已登记来源提供的 P-256 公钥指纹，严格检查编码、签名算法、DER、域和挑战摘要。限制收据为 16 KiB，拒绝重复字段及非规范版本值。壁钟和单调时钟共同约束期限，最长 120 秒，且不得超过审核到期时间。旧启动会话的挑战会被拒绝。
- 验证输出区分签名内容摘要和带签名的收据摘要。签名内容摘要可用于同一决定的幂等判断，独立于 DER 表示。真正的一次性消费仍须与任务决定写入同一事务，当前校验器只返回验证结果。工作区、任务或证据失效后的状态应在该事务内重新读取。
- `scripts/check_receipt_interop.swift` 使用 Apple CryptoKit 独立重建已签名字节。实测包含中文、引号、反斜杠、斜杠、emoji 和换行的夹具。Python 与 CryptoKit 的内容指纹一致，修改内容后签名验证失败。夹具只用临时软件密钥，不需要读取或创建 Keychain 项。P-256 与 DER 编码参考 [Cryptography API](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ec/) 和 [Apple CryptoKit P-256 公钥](https://developer.apple.com/documentation/cryptokit/p256/signing/publickey)。

验证入口仍在开发模块。`TaskManager` 和 MCP 没有新增审批入口，真实的审批提交、开工与续租仍处于锁定状态。可信签名组件、独立控制通道、受保护的公钥登记及逐次在场签名需要实机验收。PLAN 和 CONTROL 决定留待该通道验证。003E～003G 保持阶段门。

本轮实测 237 项回归通过，包含 43 项新增收据用例和 32 项 OMB-002-FIX 历史用例。实际新版 MCP 进程以本机 D3 副本完成协商、创建、查询与拒绝测试。平台复查仍为 0 个有效代码签名身份。

运行回归使用 `.venv/bin/python scripts/run_tests.py --scope full`。原始 JUnit、CryptoKit 互操作和隔离 MCP 结果随交付归档。
