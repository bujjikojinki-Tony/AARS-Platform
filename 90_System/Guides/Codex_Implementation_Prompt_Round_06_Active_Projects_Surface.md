---
title: Codex_Implementation_Prompt_Round_06_Active_Projects_Surface
type: document
status: draft
project: AARS
tags:
  - aars
  - codex
  - implementation
  - round-06
  - active-projects
created: 2026-03-28
source: ChatGPT
---

# Codex_Implementation_Prompt_Round_06_Active_Projects_Surface

Use the following prompt in Codex to implement the Active Projects Surface for the AARS Runtime MVP.

---

## Prompt

You are implementing the next bounded surface of the AARS Runtime MVP.

Your task is to build:

# **Active Projects Surface**

This surface must not be treated as a generic project list.  
It must function as a **bounded portfolio visibility surface**.

Its job is to make explicit:

- what projects are active
- which one is highest priority
- what state each project is in
- what its stable anchor status is
- what the next step is
- which projects should not currently be touched

---

## 1. Working Goal

Implement a bounded MVP surface that allows a user to immediately understand:

1. Which projects are currently active?
2. Which one is highest priority?
3. What is the current status of each project?
4. Which stable anchor exists per project?
5. What is the next step per project?
6. Which projects are frozen / paused / historical rather than active?

Do **not** build a full portfolio management app.  
Do **not** build filtering, analytics, or collaboration systems yet.

---

## 2. Implementation Target

Build a **clean, bounded, mock-data-driven portfolio surface** that emphasizes:

- project-state visibility
- priority visibility
- stable-anchor visibility
- light portfolio navigation

This surface should remain small enough to fit the MVP.

---

## 3. Required Surface

Implement:

```text id="v2pqk5"
Active Projects Surface