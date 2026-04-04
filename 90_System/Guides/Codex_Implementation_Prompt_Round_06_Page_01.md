---
title: Codex_Implementation_Prompt_Round_06_Page_01
type: document
status: draft
project: AARS
tags:
  - aars
  - codex
  - implementation
  - round-06
  - page-01
created: 2026-03-28
source: ChatGPT
---

# Codex_Implementation_Prompt_Round_06_Page_01

Use the following prompt in Codex to implement the first AARS MVP page.

---

## Prompt

You are implementing the first real UI page of the AARS Runtime MVP.

Your task is to build:

# **Page 01 — Project Overview Page**

This page is the first bounded operational surface of AARS.  
It must not be treated as a generic dashboard.  
It must function as a **governance-aware project control surface**.

---

## 1. Working Goal

Implement a **bounded MVP page** that allows a user to immediately understand:

- what project is active
- what the current objective is
- what the current health state is
- what the latest stable view is
- what the recommended next step is
- what bounded actions are admissible

Do **not** build extra pages yet.  
Do **not** build a full app.  
Do **not** build auth, database, routing complexity, or backend integration.

---

## 2. Implementation Target

Build the first page in a way that is:

- readable
- minimal
- structured
- reusable
- governance-first
- mock-data-driven

The result should be a clean page that can be run locally as an MVP UI surface.

---

## 3. Required Page

Implement:

```text
Project Overview Page