---
title: Codex_Implementation_Prompt_Round_06_Page_03
type: document
status: draft
project: AARS
tags:
  - aars
  - codex
  - implementation
  - round-06
  - page-03
created: 2026-03-28
source: ChatGPT
---

# Codex_Implementation_Prompt_Round_06_Page_03

Use the following prompt in Codex to implement the third real UI page of the AARS Runtime MVP.

---

## Prompt

You are implementing the third real page of the AARS Runtime MVP.

Your task is to build:

# **Page 03 — Review / Decision Page**

This page must not be treated as a generic notes page or summary page.  
It must function as a **governance decision surface**.

Its job is to make explicit:

- what the current review target is
- what the main findings are
- what the main weaknesses are
- what the current decision is
- why that decision was made
- what bounded next step follows

---

## 1. Working Goal

Implement a bounded MVP page that allows a user to immediately understand:

1. What is being reviewed?
2. What is the current reviewed condition?
3. What are the main findings?
4. What are the main weaknesses / risks?
5. What is the current decision?
6. What is the recommended next step?

Do **not** build unrelated pages.  
Do **not** build a workflow engine.  
Do **not** add backend logic.

---

## 2. Implementation Target

Build a **clean, bounded, mock-data-driven page** that emphasizes:

- review clarity
- decision clarity
- rationale visibility
- stable-anchor awareness
- bounded continuation logic

This page should complement:
- Project Overview
- Current Step

and complete the first MVP governance triad.

---

## 3. Required Page

Implement:

```text id="jlwmgg"
Review / Decision Page