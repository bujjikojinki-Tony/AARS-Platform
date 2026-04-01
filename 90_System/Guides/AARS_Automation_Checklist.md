---
title: AARS_Automation_Checklist
type: guide
status: draft
project: AARS
tags:
  - aars
  - automation
  - checklist
created: 2026-03-28
source: ChatGPT
---

# AARS_Automation_Checklist

## 1. Purpose

This checklist provides a practical control routine for automation in AARS.

It is intended to:
- turn the automation operating model into an operational checklist
- distinguish safe automation from unsafe automation
- ensure automation remains bounded, reviewable, and continuity-aware
- reduce risk of Codex or script-driven structural drift

This is an operational checklist, not an automation theory note.

---

## 2. Core Automation Rule

Before running automation, confirm:

**this task automates repetition, not judgment**

If the task requires:
- strategic scope change
- freeze authority
- archive authority
- major baseline promotion
- cross-project restructuring

then it should remain human-gated.

---

## 3. Automation Output States

Every automation should end in one of the following:

- **No-op**
- **Bounded changes applied**
- **Report generated**
- **Review required before apply**
- **Blocked**
- **Aborted by rule**

Automation should not end in silent mutation.

---

## 4. Universal Automation Checklist

Use this before any serious automation.

### A. Scope Check
- [ ] Is the target project or directory explicit?
- [ ] Is the automation bounded to specific files or folders?
- [ ] Are out-of-scope areas explicitly excluded?

### B. Governance Check
- [ ] Does the task avoid human-gated decisions?
- [ ] Does the task avoid auto-freeze, auto-archive, and auto-promotion?
- [ ] Does the task respect the current Latest Stable View?

### C. Continuity Check
- [ ] Is the current stable anchor known?
- [ ] Can the result be compared against the prior state?
- [ ] Is rollback or recovery possible if the result is wrong?

### D. Output Check
- [ ] Will the automation produce visible outputs, logs, or reports?
- [ ] Will the result be reviewable?
- [ ] Will the updated files remain structurally interpretable?

---

## 5. Safe Structural Automation Checklist

Use this for tasks like:
- frontmatter normalization
- index refresh
- MOC update
- file naming normalization
- directory hygiene checks

### Safe Structural Conditions
- [ ] The task is repetitive
- [ ] The target files are clearly bounded
- [ ] No semantic reinterpretation is required
- [ ] The task does not alter project scope
- [ ] The task does not change baseline state

### Decision
- [ ] Safe to automate
- [ ] Review before apply
- [ ] Do manually instead

---

## 6. Objectization Automation Checklist

Use this for:
- scaffolding capability files
- scaffolding invocation files
- scaffolding dependency/risk/health files
- generating template-based object drafts

### Objectization Checks
- [ ] The object type is known
- [ ] The schema or expected structure is known
- [ ] The project or case scope is known
- [ ] The automation is creating structure, not declaring maturity
- [ ] Review will occur after generation

### Rule
Automation may create draft objects, but should not silently declare them stable.

---

## 7. Review Automation Checklist

Use this for:
- review checklist generation
- stale file scan
- missing link scan
- object-chain completeness scan
- baseline comparison reports

### Review Automation Checks
- [ ] The automation reports findings rather than final judgments
- [ ] Human review remains possible
- [ ] Findings are tied to explicit files or objects
- [ ] The task does not overstate certainty

### Rule
Monitoring may be automated; governance judgment remains bounded.

---

## 8. Cross-Project Automation Checklist

Use this for any automation touching more than one project.

### Cross-Project Checks
- [ ] The affected projects are explicitly listed
- [ ] The automation will not merge project-local states unintentionally
- [ ] Shared system files and project files remain distinguishable
- [ ] The task will not cross-write stable anchors from one project into another

### Rule
Cross-project automation is higher risk and should default to review-first behavior.

---

## 9. Stable View Sensitive Automation Checklist

Use this when automation affects:
- stable view files
- continuity logs
- freeze notes
- active project baselines

### Stable View Checks
- [ ] Current Latest Stable View is known
- [ ] The automation will not silently replace the current stable anchor
- [ ] A visible comparison or report will exist
- [ ] Recovery remains possible if the new output is worse

### Rule
Automation should treat stable-view-sensitive files as protected assets.

---

## 10. Freeze / Archive Sensitive Automation Checklist

Use this when automation could affect:
- frozen baselines
- archived assets
- active-to-archive transitions
- stable-to-frozen transitions

### Sensitive Checks
- [ ] Is a human explicitly approving this action?
- [ ] Is the current baseline state known?
- [ ] Is the action changing storage only, or also governance meaning?
- [ ] Is a trace note being created?

### Rule
Automation should not autonomously decide freeze or archive status for major assets.

---

## 11. Pre-Run Checklist

Before running automation, ask:

1. What exactly will this touch?
2. What should it not touch?
3. What baseline state does it assume?
4. What should happen if conflict appears?
5. What visible output will it leave behind?

If these are unclear, do not run.

---

## 12. Post-Run Checklist

After automation runs, ask:

1. Did it stay within scope?
2. Did it create the expected outputs?
3. Did it preserve interpretability?
4. Did it avoid touching protected assets?
5. Is review now required before continuation?

Automation is not complete just because it finished.

---

## 13. Automation Red Flags

Treat automation as unsafe if any of the following are true:

- [ ] the target scope is vague
- [ ] it touches multiple active projects without explicit design
- [ ] it updates frozen baselines automatically
- [ ] it changes governance states implicitly
- [ ] it rewrites stable-view-sensitive files without comparison
- [ ] it produces no visible report

---

## 14. Minimal Automation Summary Template

Use this short form to document a run.

### Automation Target
[project / system / directory / object class]

### Scope
[which files/folders]

### Protected Areas
[which files/folders must not change]

### Expected Outcome
[normalize / scaffold / report / refresh / compare]

### Actual Outcome
[ ]

### Review Needed?
[yes / no]

### Next Step
[ ]

---

## 15. Final Rule

AARS automation is acceptable only when it:
- stays bounded
- preserves continuity
- leaves visible trace
- avoids hidden governance decisions
- improves consistency without weakening control