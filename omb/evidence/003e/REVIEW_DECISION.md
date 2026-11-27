# OMB-003E 初始化边界验收

本轮修复启动器首次初始化竞态，并补齐异常配置处理。源码基于 e016103，修改尚未提交；本包仅供审查，不是部署发布包。

- 独立初始化文件锁使用非阻塞排他锁。锁被占用时返回 LAUNCHER_INITIALIZING，且不创建数据库。
- 初始化中断仅留下绑定文件时，下次启动返回 INTEGRITY_FAILURE；保留原文件，不删除历史或自动重建身份。该测试使用明确注入的创建异常，不宣称完成整机断电测试。
- 命名管道不阻塞配置读取；断链、超大配置、重复 JSON 字段被拒绝。子进程实测在8秒超时内退出，标准输出为空，标准错误无堆栈。
- 前轮身份、权限、硬链接、单协调器、重启持久化测试全部保留。

全量回归 328/328，通过32项历史测试及296项开发测试。四项冻结输入哈希一致。实际 MCP 进程验收重跑仍有5项完整 PASS、2项部分验证和1项契约不满足；脚本正确退出3，未将其当作成功退出。

剩余应用内联调、界面显示为 PENDING；未知协议版本的明确拒绝条款与 SDK 协商行为仍有差异；审批平台 BLOCKED。003E 总裁决 BLOCKED。003F、003G HOLD，不能冻结。

复现：在原独立工作区运行 .venv/bin/python scripts/run_tests.py --scope full。进程验收使用 PYTHONPATH=src:frozen_payload/source/src .venv/bin/python scripts/check_003e_mcp.py。本包 changes/ 保存完整变更文件，CHANGE.patch 是相对基准提交的已跟踪产品代码差异；新增文件以 changes/ 为准。

未修改 OpenMausBot 配置或运行冻结库，未进行 Apple Developer 设置。
