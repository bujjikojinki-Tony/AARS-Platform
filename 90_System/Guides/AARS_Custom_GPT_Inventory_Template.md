---
title: AARS Custom GPT Inventory Template
type: template
status: stable
project: AARS
tags:
  - aars
  - system
  - guide
  - inventory
  - gpt
created: 2026-03-25
source: curated system governance guide
area: system
aliases:
  - AARS Custom GPT Inventory
  - AARS Custom GPT Inventory 表格模板
related:
  - "[[90_System/MOCs/AARS_Home]]"
  - "[[AARS_Content_Governance_Self_Check_Prompts]]"
---

# AARS Custom GPT Inventory

## 目的

用于盘点当前已有的 AARS 相关 Custom GPT，并判断每一个 GPT 及其关联 [[AARS_vNext_Terminology_Glossary#Artifact|资产]] 应该：

- 保留
- 合并
- 转入 Project
- 沉淀到 Obsidian
- 归档
- 退役

---

## 一、总表

| GPT名称 | 当前用途 | 主要内容类型 | 是否跨项目复用 | 是否依赖单一项目上下文 | 是否有固定输出格式 | 是否有Knowledge文件 | 是否有Actions/Apps | 当前状态 | 建议处理 |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| AARS Architect | OS架构设计 | 角色能力/规范 | 是 | 否 | 是 | 是 | 否 | 使用中 | 保留 |
| AARS Reviewer | 审查与一致性检查 | 角色能力/检查规则 | 是 | 否 | 是 | 是 | 否 | 使用中 | 保留 |
| AARS Knowledge Curator | 术语与模板整理 | 角色能力/知识治理 | 是 | 否 | 是 | 是 | 否 | 使用中 | 保留 |
| CDA Project GPT | CDA项目推进 | 项目上下文 | 否 | 是 | 一般 | 是 | 否 | 使用中 | 转入Project |
| Nuclear Study GPT | 核电专题研究 | 项目上下文/专题研究 | 否 | 是 | 一般 | 是 | 否 | 低频 | 转入Project |
| 某论文投稿GPT | 投稿流程支持 | 项目上下文/阶段产物 | 否 | 是 | 是 | 是 | 否 | 阶段性 | Project + Archive |

---

## 二、单个 GPT 评估模板

### GPT 名称
`填写名称`

### 1. 基本信息
- 当前用途：
- 创建目的：
- 最近一次使用时间：
- 当前状态：使用中 / 低频 / 闲置 / 待退役

### 2. 内容性质判断
- 主要属于：
  - 角色能力
  - 项目上下文
  - 长期知识资产
  - 模板/规范
  - 过程记录
  - 其他
- 次级属性：
- 是否跨项目复用：是 / 否
- 是否强依赖某个单一项目：是 / 否
- 是否强依赖近期对话上下文：是 / 否

### 3. 结构能力判断
- 是否有固定输出格式：是 / 否
- 是否有稳定角色定位：是 / 否
- 是否有清晰审查规则：是 / 否
- 是否有上传 knowledge 文件：是 / 否
- 是否有 actions / apps / 外部工具：是 / 否

### 4. 资产拆解
#### Instructions
- 是否值得保留在 GPT：
- 是否应迁入 Project instructions：
- 是否应沉淀为文档模板：

#### Knowledge
- 是否应迁入 Obsidian：
- 推荐目录：
- 推荐文档类型：

#### Output Format
- 是否应抽取为模板：
- 推荐模板名称：

### 5. 去向判断
- 是否继续保留为 Custom GPT：是 / 否
- 是否应转入 ChatGPT Project：是 / 否
- 是否应沉淀到 Obsidian：是 / 否
- 是否应 Archive：是 / 否
- 是否应 Retire：是 / 否

### 6. 最终建议
- 建议处理：保留 / 合并 / 转入Project / 沉淀到Obsidian / Archive / Retire
- 理由：
- 后续动作：

---

## 三、处理规则速查

| 情况 | 建议去向 |
|---|---|
| 长期稳定角色能力 | 保留为 Custom GPT |
| 当前专题项目工作区 | 转入 ChatGPT Project |
| 术语、规范、Kernel、Schema、Template | 沉淀到 Obsidian |
| 阶段性 review / checklist / submission 过程 | Project 或 Archive |
| 过时、重复、低价值 GPT | Retire |

---

## 四、建议最终保留的核心 GPT

| GPT名称 | 核心职责 |
|---|---|
| AARS Architect | OS vNext 架构、Kernel、Schema、Spec |
| AARS Research Planner | 研究问题拆解、路线图、Capability Graph |
| AARS Reviewer | 一致性检查、投稿审查、Checklist |
| AARS Knowledge Curator | 术语、模板、知识治理、迁移建议 |

---

## 五、推荐执行顺序

1. 列出全部现有 GPT  
2. 逐个填写“单个 GPT 评估模板”  
3. 优先保留 3–4 个核心角色型 GPT  
4. 将项目型 GPT 转入 ChatGPT Project  
5. 将知识型内容迁入 Obsidian  
6. 将重复和过时 GPT 归档或退役
