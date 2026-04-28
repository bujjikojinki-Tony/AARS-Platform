# HMI Cross-Domain Guideline Package v0.3

本文件包用于沉淀面向高可靠计算机界面的人机接口（HMI/HSI）设计导则。研究基线来自核电、船舶、航空航天及通用 HCI/告警管理规范，并转化为可用于项目设计、页面评审、AI/自动化界面治理和监控台重构的 Markdown 文档包。

## Package Structure

```text
90_System/
  Knowledge/
    Human_Factors/
      01_HMI_Cross_Domain_Standards_Study_v0.md

  Guides/
    HMI/
      02_HMI_Design_Principles_v0.md
      03_HMI_Information_Architecture_Guideline_v0.md
      04_HMI_Alarm_Degraded_Mode_Guideline_v0.md
      05_HMI_Automation_AI_Interface_Guideline_v0.md
      06_HMI_Design_Review_Checklist_v0.md

templates/
  HMI_Terminology_Glossary_v0.md
  HMI_Page_Task_Model_Template_v0.md
  HMI_Alarm_Object_Template_v0.md
  HMI_Recovery_Path_Template_v0.md
  HMI_AI_Recommendation_Card_Template_v0.md

project_examples/
  Weather_Multi_Market_Console/
    Weather_Multi_Market_Console_HMI_Design_v0.md
    Weather_Multi_Market_Console_Page_Task_Model_v0.md
    Weather_Multi_Market_Console_Review_Gate_v0.md
```

## Latest Stable View

高可靠计算机界面不是普通 dashboard，而是“任务态势 + 风险告警 + 操作门控 + 自动化透明 + 降级恢复 + 审查证据”的人机协同控制台。

## Suggested Obsidian Placement

系统级知识：

```text
90_System/Knowledge/Human_Factors/
```

系统级导则：

```text
90_System/Guides/HMI/
```

项目级副本：

```text
03_Projects/<Project_Name>/Guides/HMI/
```

## Version

- Package: HMI_Cross_Domain_Guideline_Package_v0.3
- Status: Draft baseline, ready for project-level adaptation
