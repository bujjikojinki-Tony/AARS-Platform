# OMB-003C 事件与 Evidence 集成

当前状态为 `READY_FOR_003C_CODE_REVIEW`。父提交为 OMB-003B `7e659cbcb8347572fb05090b193929c3248f208f`。本阶段继续在独立开发环境内验证，审批 broker、新 MCP、实机部署和发布验收分别保留在后续阶段。

| 验证项 | 实际结果 |
|---|---|
| 完整回归 | 175 通过，0 失败，0 跳过。含 17 项 003C 用例、126 项延续的 003B 用例及 32 项 002 历史用例 |
| 冻结证据登记 | 逐项校验归档中 9 个原始合成对象，使用现有 SDK 认证完整引用图。保留原始 `sha256:unavailable` 来源标记 |
| 任务追溯 | 核对 link → 任务版本 → 事件 → Core Evidence → Observation。关联、版本和事件在同一 SQLite 事务提交 |
| 权限与用途 | 独立 `evidence.link` 和 `task.work` 能力、任务范围、版本、状态和有效租约。原 003B 绑定迁移后需另行配置本能力。只允许本机合成验证用途 |
| 失效处理 | 已记录的撤销和过期不因重放、重启或时钟回拨重新生效。失效追加历史版本。未持久化的时钟过期会立即影响追溯读取和新关联，由宿主复核或重启写入失效事件 |
| 数据库迁移 | 实际 003B 开发库以 SQLite backup API 复制到私有 C2 目录。原库 SHA256、原任务快照及原事件指纹相同。证据记录在重开后再次校验 |

冻结合成图 `BOT_TASK_OBJECT_SNAPSHOT.json` 是当前登记器唯一认可的来源。归档字节 SHA256 与对象指纹代表不同层次。已校验的本机合成夹具只登记一套图，外部来源、对象内容更新及 `supersedes` 因缺少已准入的新来源而仍未开放。目录 `PENDING` 和真实数据的授权仍遵从原流程。

`TaskRuntime.register_frozen_fixture()` 和 `revoke_frozen_fixture(reason)` 属于可信 Python 宿主能力，不进入 Bot 命令表。`TaskManager.execute('evidence_link', ...)` 消费引用，`TaskManager.evidence_trace(task_id)` 按权限读取历史版本、事件、归档指纹和 Core 来源。对任务定义、期限、用途和来源的核对不授予生产执行。完整性失败进入已有隔离流程。事件采用同库追加与读时核对，未来外发需要独立的投递契约。

正向关联用例通过明确标注的测试前置状态构造 RUNNING 与租约。实际开发演示只登记归档和核验迁移后的历史任务，启动与人工审批保持 `APPROVAL_LOCKED`，审核请求仍处于 `PHASE_HOLD`。本轮未覆盖未来阶段的 OpenMausBot/Magpie 实机门。

迁移要求 003B 开发库已停止，且有既有私有运行锁文件。使用 `aars_task_manager.migration.migrate_b1_copy` 提供不同的目标私有目录及受保护的根目录。已有目标、活跃源和损坏历史均拒绝。源库继续可供 003B 读取，C2 不可用时可切回 B1 原库并保留 C2 证据，不涉及 002 冻结运行目录。

运行回归时从仓库目录执行 `.venv/bin/python scripts/run_tests.py --scope full`。开发依赖与 003B 相同。旧范围守卫中“关联保持 HOLD”一项随 003C 实现被关联契约测试取代，审核请求的 HOLD 检查保留。冻结的 32 项历史测试原样运行。实现涵盖本阶段基础用例，80 项跨阶段设计矩阵仍按各阶段实际取证。
