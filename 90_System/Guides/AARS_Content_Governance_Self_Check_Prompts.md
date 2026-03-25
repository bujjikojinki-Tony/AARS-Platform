# AARS 内容治理自查提示词手册

## 目的

本手册用于判断以下内容应如何处理：

- 是否继续保留在 Custom GPT
- 是否转入 ChatGPT Project
- 是否沉淀到 Obsidian
- 是否同时进入 Project 与 Obsidian
- 是否应归档或退役

适用场景：

- AARS Research OS vNext
- CDA / Nuclear / OpenClaw / TREM2 等专题项目
- 旧 ChatGPT 对话内容
- 旧 Custom GPT 中的 instructions / knowledge / templates
- 阶段性输出、review、roadmap、submission checklist

---

## 总体判断原则

### 1. 角色能力
适合保留在 Custom GPT。

典型特征：
- 长期稳定
- 跨项目复用
- 固定规则、固定输出风格、固定审查标准
- 不依赖某一轮具体聊天上下文

### 2. 当前项目上下文
适合转入 ChatGPT Project。

典型特征：
- 与某个项目当前推进阶段直接相关
- 依赖近期对话与文件上下文
- 会随项目阶段变化而频繁更新
- 更像工作区材料而不是长期知识资产

### 3. 长期知识资产
适合沉淀到 Obsidian。

典型特征：
- 长期有效
- 可复用、可引用、可双链
- 不依赖单次对话上下文
- 适合作为 Markdown 文档长期保存

### 4. 过程性内容
一般进入 Project 或 Archive，不直接当长期知识。

典型特征：
- 中间草稿
- 阶段记录
- review 过程
- 临时讨论
- 某轮版本说明

### 5. 模板、术语、规范、Kernel、Schema
优先沉淀到 Obsidian。

---

## 可选归属类型

- 保留在 Custom GPT
- 转入 ChatGPT Project
- 沉淀到 Obsidian
- Project + Obsidian
- Archive
- Retire

---

## 一、总控版自查提示词

```text
你现在扮演 AARS 内容治理审查器。

你的任务是审查我提供的这段内容，判断它目前是否仍适合继续留在 ChatGPT 对话或 Custom GPT 中，还是应该转入 ChatGPT Project，或者沉淀到 Obsidian。

请严格按以下维度逐项审查：

1. 内容性质
- 它属于：角色能力 / 项目上下文 / 长期知识资产 / 模板规范 / 过程记录 / 临时草稿 / 历史归档 / 其他？
- 请给出主类别和次类别。

2. 时效性
- 这是短期有效还是长期有效？
- 它是否高度依赖当前项目阶段、当前轮对话、某次具体任务？
- 如果脱离当前上下文，它是否仍然有价值？

3. 复用性
- 它是否会跨多个项目复用？
- 它是否适合长期反复调用？
- 它是否只是某一个专题或某一轮工作专用？

4. 稳定性
- 这段内容是否已经稳定？
- 是否仍频繁变化？
- 是否更像“正在讨论中的过程”，而不是“已经沉淀的资产”？

5. 最佳归属
请从以下位置中选择最合适的归属，并解释理由：
- 保留在 Custom GPT
- 转入 ChatGPT Project
- 沉淀到 Obsidian
- 同时进入 Project 和 Obsidian
- 归档
- 退役删除

6. 输出格式
请最后输出以下结构：
- 内容类型：
- 是否仍适合留在 GPT：
- 是否应转入 Project：
- 是否应沉淀到 Obsidian：
- 是否应归档：
- 判断理由：
- 推荐动作：
- 推荐文件名（如果进入 Obsidian）：
- 推荐目录（如果进入 Obsidian）：
- 推荐项目位置（如果进入 Project）：

判断时遵循以下原则：
- 角色能力优先留在 GPT
- 当前项目上下文优先进入 Project
- 长期知识、术语、规范、模板优先进入 Obsidian
- 过程性内容不应直接当作长期知识
- 如果同时具备“当前项目使用价值”和“长期知识价值”，则可以同时进入 Project 和 Obsidian，但要区分版本和用途

现在开始审查我接下来提供的内容。