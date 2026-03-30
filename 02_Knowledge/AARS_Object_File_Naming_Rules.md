---
title: AARS_Object_File_Naming_Rules
type: guide
status: draft
project: AARS
tags:
  - aars
  - naming
  - object
  - file-rules
created: 2026-03-28
source: ChatGPT
---

# AARS_Object_File_Naming_Rules

## 1. Purpose

This guide defines file naming rules for AARS object files, project files, system files, and continuity assets.

It is intended to:
- reduce naming drift
- improve cross-file clarity
- make object type visible from filename
- support Obsidian navigation and Git-based maintenance
- improve Codex-assisted normalization and automation

This is a file naming guide, not a system model.

---

## 2. Core Naming Principle

The core principle is:

**filenames should reveal scope, function, and object role with minimal ambiguity**

A good AARS filename should help answer:
- what this file is
- what scope it belongs to
- whether it is project-level or system-level
- whether it is a governed object, guide, review note, or baseline

---

## 3. General Naming Rules

Use the following general rules:

1. Prefer clear words over clever short names  
2. Use `_` between words when needed for consistency  
3. Keep names stable once linked across many notes  
4. Include project or case identifiers when the file is local rather than global  
5. Make object type visible where practical  
6. Avoid vague names like:
   - `note1`
   - `draft_final`
   - `new_version`
   - `misc`
   - `important_file`

---

## 4. System-Level File Naming

System-level files should begin with:

```text
AARS_