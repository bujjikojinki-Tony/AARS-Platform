---
title: Codex_Implementation_Prompt_Round_06_Page_02
type: document
status: draft
project: AARS
tags:
  - aars
  - codex
  - implementation
  - round-06
  - page-02
created: 2026-03-28
source: ChatGPT
---

# Codex_Implementation_Prompt_Round_06_Page_02

Use the following prompt in Codex to implement the second real UI page of the AARS Runtime MVP.

---

## Prompt

You are implementing the second real page of the AARS Runtime MVP.

Your task is to build:

# **Page 02 — Current Step Page**

This page must not be treated as a generic task page.  
It must function as a **bounded current-step control surface**.

Its job is to make the current step operationally legible.

---

## 1. Working Goal

Implement a bounded MVP page that allows a user to immediately understand:

- what step is current
- what the current step is trying to achieve
- what has already been completed
- what remains open
- what is blocked
- what the immediate next step is

Do **not** build other pages yet.  
Do **not** turn this into a workflow engine.  
Do **not** build backend logic.

---

## 2. Implementation Target

Build a **clean, bounded, mock-data-driven page** that emphasizes:

- progression clarity
- bounded execution awareness
- blocker visibility
- next-step control

This page should complement the Project Overview page, not replace it.

---

## 3. Required Page

Implement:

```text id="brd3bj"
Current Step Page