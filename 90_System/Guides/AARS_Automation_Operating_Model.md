---
title: AARS_Automation_Operating_Model
type: guide
status: draft
project: AARS
tags:
  - aars
  - automation
  - operating-model
created: 2026-03-28
source: ChatGPT
---

# AARS_Automation_Operating_Model

## 1. Purpose

This document defines how automation should be used inside AARS.

It explains:
- what kinds of work can be safely automated
- what kinds of work must remain human-gated
- how ChatGPT, Codex, Obsidian, and GitHub should interact under automation
- how bounded progression should be preserved even when repeated tasks are delegated

This is not a tool-specific setup manual.  
It is an operating model for automation inside AARS.

---

## 2. Core Automation Principle

The core principle is:

**automate repetition, not judgment**

AARS should automate:
- repetitive normalization
- repetitive synchronization
- repetitive structure maintenance
- repetitive monitoring
- repetitive check routines

AARS should not fully automate:
- project intent setting
- final scope decisions
- final acceptance decisions
- freeze authority
- strategic tradeoff judgment

Automation must remain subordinate to governance.

---

## 3. Automation Goal

Automation in AARS exists to reduce:
- manual repetition
- structural inconsistency
- file drift
- delayed review signals
- stale navigation artifacts
- weak continuity maintenance

Automation does **not** exist to replace bounded human control.

---

## 4. Automation Layers

Automation should operate across four layers:

1. Knowledge Automation  
2. Repository Automation  
3. Objectization Automation  
4. Review and Monitoring Automation  

These should be introduced progressively, not all at once.

---

## 5. Knowledge Automation

## Purpose
Keep knowledge assets structurally consistent.

## Suitable Tasks
- add or normalize frontmatter
- update links in MOC pages
- regenerate `INDEX.md`
- maintain glossary/taxonomy cross-links
- move inbox files to candidate target locations
- apply naming conventions

## Unsuitable Tasks
- invent new strategic categories without review
- rewrite stable knowledge documents without supervision
- merge conceptually different files automatically

## Rule
Knowledge automation should support structure, not redefine meaning.

---

## 6. Repository Automation

## Purpose
Keep the repository operational and synchronized.

## Suitable Tasks
- auto commit-and-sync
- worktree-safe execution
- scheduled repository scans
- branch-safe file generation
- directory hygiene checks
- stale file detection

## Unsuitable Tasks
- force-push history rewrites
- autonomous branch deletion
- large-scale renaming without review
- automatic archival of files with uncertain status

## Rule
Repository automation should preserve recoverability.

---

## 7. Objectization Automation

## Purpose
Turn repeatable prose outputs into governed object files where appropriate.

## Suitable Tasks
- scaffold capability objects from catalog entries
- scaffold invocation records from bounded case notes
- scaffold dependency/risk/health objects from structured prompts
- generate object templates from known schemas
- update object registries and index pages

## Unsuitable Tasks
- declare an object “stable” without review
- auto-promote draft analysis into formal object status
- infer high-confidence governance decisions from weak evidence

## Rule
Automation may prepare objects, but human or governance review should validate them.

---

## 8. Review and Monitoring Automation

## Purpose
Increase visibility of system state and emerging issues.

## Suitable Tasks
- scheduled glossary consistency checks
- missing frontmatter checks
- missing-link detection
- stale project-home detection
- object-chain completeness checks
- open review-item checklists
- update latest known review dashboard

## Unsuitable Tasks
- final acceptance judgment
- full replacement of review notes
- autonomous freeze decisions
- autonomous continuation across major uncertainty

## Rule
Monitoring can be automated; governance decisions remain bounded.

---

## 9. Human-Gated Decisions

The following decisions should remain explicitly human-gated:

1. project creation
2. scope boundary changes
3. non-goal changes
4. major capability-family expansion
5. freeze decision
6. archive decision
7. major recovery branch decision
8. final publication readiness decision

Automation may support these decisions, but must not silently make them.

---

## 10. GPT / Codex / Obsidian / GitHub Division Under Automation

## ChatGPT
### Best Role
- produce automation prompts
- define rules
- review outputs
- classify tasks
- judge whether automation is appropriate
- recommend next-step decisions

### Not Ideal For
- direct background repository mutation
- unsupervised large-scale file restructuring

---

## Codex
### Best Role
- run repetitive repository tasks
- generate structured files
- normalize Markdown
- update indexes and MOCs
- run automations on schedule
- use worktrees for safe isolation

### Not Ideal For
- final strategic governance decisions
- unconstrained knowledge redesign

---

## Obsidian
### Best Role
- display stable notes
- preserve knowledge state
- provide knowledge navigation
- serve as the human review surface
- support local automation via notes, links, and URI patterns

### Not Ideal For
- large-scale repository execution logic
- deep background orchestration

---

## GitHub
### Best Role
- version history
- rollback
- branch management
- PR-based review support
- audit trail

### Not Ideal For
- semantic judgment
- content governance by itself

---

## 11. Recommended Automation Classes

AARS should define automation in three classes.

### Class A — Safe Structural Automation
These are safe to automate with minimal review:
- frontmatter normalization
- MOC regeneration
- index updates
- commit-and-sync
- stale link checks

### Class B — Reviewable Object Automation
These may be automated, but should be reviewed:
- object scaffolding
- inbox classification
- taxonomy/glossary alignment suggestions
- dependency/risk draft generation
- review checklist generation

### Class C — Human-Gated Governance Automation
These may be supported but not fully automated:
- freeze recommendation
- recovery recommendation
- scope change recommendation
- next-phase branching recommendation

---

## 12. Automation Entry Conditions

No automation should run unless the following are known:

- which project it belongs to
- which directory/repo it can modify
- whether it runs in local or isolated mode
- what files are in scope
- what files are out of scope
- what action is allowed if conflicts appear

This prevents uncontrolled runtime drift.

---

## 13. Automation Exit Conditions

Every automation should end with at least one of the following outputs:

- files updated
- report generated
- review note generated
- no-op conclusion
- conflict or blocker report
- handoff back to human review

Automation should not end in silent state mutation without visible trace.

---

## 14. Automation and Worktrees

Wherever possible, automation should run in isolated worktrees rather than directly in the main working directory.

This is especially important when:
- generating many files
- restructuring navigation
- updating system-wide links
- drafting object chains

The goal is to preserve rollback and comparison safety.

---

## 15. Recommended First-Wave Automations

For the current AARS setup, the most appropriate first-wave automations are:

### Automation 1 — Inbox Normalization
- scan `00_Inbox`
- classify files
- suggest destinations
- scaffold frontmatter
- produce migration report

### Automation 2 — MOC / Index Refresh
- refresh `INDEX.md`
- refresh `AARS_System_Home.md`
- refresh project home pages

### Automation 3 — Glossary / Taxonomy Consistency Check
- detect missing core terms
- detect label drift
- detect mismatch between glossary and taxonomy usage

### Automation 4 — Object Chain Completeness Check
- check whether a bounded case has:
  - invocation
  - dependency
  - risk
  - health
  - stable view
  - recovery/no-recovery

### Automation 5 — Stable Baseline Refresh Check
- identify candidate frozen baselines
- produce review-needed report
- do not auto-freeze

---

## 16. Automation Failure Modes

Automation can fail in several ways:

### Failure 1 — Structural Overreach
Automation begins changing more files than intended.

### Failure 2 — Governance Bypass
Automation silently performs actions that should have required review.

### Failure 3 — Drift Amplification
Automation repeats a bad structure consistently.

### Failure 4 — False Precision
Automation produces overly formal but weakly justified objects.

### Failure 5 — Hidden Mutation
Automation changes important files without clear traceability.

### Failure 6 — Premature Closure
Automation incorrectly implies that a project is stable or complete.

---

## 17. Anti-Failure Rules

To reduce the above risks:

1. automate in bounded directories
2. prefer worktree execution
3. require visible reports
4. preserve latest stable view before major automation
5. do not auto-freeze
6. do not auto-archive
7. keep scope files human-reviewed
8. separate automation reports from governance decisions

---

## 18. Minimal Automation Workflow

A minimal safe AARS automation loop is:

```text
Define task boundaries
→ Run automation in bounded scope
→ Produce visible report
→ Review results
→ Accept / revise / reject
→ Capture into knowledge layer