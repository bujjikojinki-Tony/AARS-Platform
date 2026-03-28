---
name: codex-verify-playbook
description: Use when the user wants a verification-first Codex pass: review a change, hunt for regressions, identify test gaps, and close with a concise risks-and-validation summary.
---

# Codex Verify Playbook

Use this skill when the job is primarily to review, validate, or de-risk work that already exists.

## Quick Start

1. Identify the change surface:
   - changed files
   - user-visible behavior
   - hidden risk areas such as state, auth, migrations, and edge cases
2. Decide the verification method:
   - code review
   - targeted tests
   - manual scenario checks
   - a combination of the above
3. Prioritize findings by severity and likelihood.
4. End with what was verified, what was not, and the sharpest next step.

## Review Workflow

### 1. Scope

Start by naming:
- what changed
- what could regress
- which files or systems deserve the closest read

### 2. Findings First

When issues exist, present them before summaries:
- prioritize bugs, behavioral regressions, unsafe assumptions, and missing tests
- include precise file references when possible
- keep findings concrete and actionable

If no issues are found, say that explicitly and still call out residual risk or coverage gaps.

### 3. Verification Depth

Choose the lightest process that still earns confidence:
- read-only review for obviously scoped doc or config changes
- targeted tests for code-path changes
- manual scenario notes when automation is absent

Do not claim validation you did not perform.

### 4. Closeout Format

Return:
- findings or a clear no-findings statement
- verification performed
- residual risks
- recommended next action

## Guardrails

- Review the code that actually changed instead of reciting generic best practices.
- Avoid low-signal commentary when no real issue exists.
- Prefer high-confidence findings over speculative noise.
- Distinguish confirmed behavior from inference.
