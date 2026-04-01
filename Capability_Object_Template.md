---
title: Capability_Object_Template
type: template
status: draft
project: AARS
tags:
  - aars
  - capability
  - template
created: 2026-03-28
source: ChatGPT
---

# Capability_Object_Template

## 1. Purpose

This template provides the standard Markdown structure for an AARS capability object.

It is intended to:
- make capability formalization repeatable
- reduce structural drift across capability files
- support review, lifecycle tracking, and Codex-assisted generation
- provide a bounded starting structure for reusable operational units

This is a reusable object template.

---

## 2. Use Rule

Use this template when:
- a recurring operation should become a formal capability
- a candidate capability has moved beyond loose description
- a pilot needs a first-wave capability family
- a project is preparing for bounded case execution

Do not use this template for:
- generic topic notes
- one-off tasks
- review notes
- bounded case files

---

## 3. Recommended File Name

Preferred naming pattern:

```text id="wovggt"
CAP-<DOMAIN>-<NUMBER>_<Capability_Name>.md