# OMB-003 补验裁决

本记录更新 2026-11-28 收口报告。总裁决保持 `BLOCKED`。003E 的配置切换子项通过，003F、003G 的正式阶段门保持 `HOLD`。

| 验收项 | 本轮累计结论 | 主要证据 |
|---|---|---|
| TM-MAC-04 应用重启 | `PARTIAL`。真实应用重启后读回草稿和事件。Evidence 持久化已通过独立 stdio 与数据库补验，应用内读回仍待实测。 | `OMB_003_EVIDENCE_STDIO_RETEST.md` 与既有应用重启记录 |
| TM-MAC-06 本人在场审批 | `BLOCKED_APPROVAL_PLATFORM`。复查发现 0 个有效签名身份。正式签名双向 XPC、受信公钥激活与在场审批未完成。 | 003D F-02 收口与本轮签名库存复查 |
| TM-MCP-08 界面边界 | `PARTIAL`。已有无害文本显示和单次数据内指令隔离记录。Evidence 界面渲染和 HTML 执行隔离仍待补证。 | `OMB_003E_UI_BOUNDARY_REVIEW` |
| TM-RELEASE-01 源码与证据绑定 | `PASS_REVIEW_REPRODUCTION`。从固定审查快照及两份补验补丁复现 330 项测试。正式签名候选清单待验。 | `REPRODUCED_330_EVIDENCE.json` |
| TM-RELEASE-02 包完整性 | `PASS_REVIEW_PACKAGE`。156 个条目已校验，解包后 328 项快照回归通过。正式发布包待验。 | `OMB_003_REVIEW_PACKAGE_VERIFICATION.md` |
| TM-RELEASE-03 迁移失败回滚 | `PASS_ISOLATED_REHEARSAL`。模拟发布 I/O 失败后 D4 原库完整，重试成功。 | `OMB_003_ROLLBACK_RETEST.md` |
| TM-RELEASE-04 旧版与备份回滚 | `PASS_ISOLATED_REHEARSAL`。实际 b8 打开恢复后的 D4，D5 新事件从归档副本读回。 | `OLD_READER_ROLLBACK_EVIDENCE.json` |
| TM-RELEASE-05 停用 003 回 002 | `PASS_APP_CONFIG_SWITCH`。观察到桌面应用的实际停用和恢复。002 原启动器健康并校验 9 个对象。003 历史通过实际 MCP 进程在一致性副本上读回。 | `OPENMAUSBOT_SWITCH_DISABLED.json` 与 `OPENMAUSBOT_SWITCH_RESTORED.json` |
| TM-RELEASE-08 最终冻结 | `BLOCKED`。正式审批与其他未通过的实机及界面项目仍需证据。 | 本记录和既有各阶段裁决 |

完整回归复现为 330/330 通过，失败、错误、跳过均为零。此前审查包的 328 项对应包内原快照，另两项来自包内归档的补丁。
