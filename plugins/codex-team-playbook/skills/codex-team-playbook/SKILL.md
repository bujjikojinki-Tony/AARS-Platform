---
name: codex-team-playbook
description: Use when the user wants a team-mode workflow for Codex: plan a task, split it into clean workstreams, decide whether delegation is appropriate, and close with verification and handoff notes. Inspired by oh-my-claudecode, but adapted to Codex agent rules.
---

# Codex Team Playbook

Use this skill for complex implementation, review, migration, or research tasks that benefit from a clear plan and team-style execution.

## Quick Start

1. Restate the goal, constraints, and expected output in 2-4 lines.
2. Create a short team brief before editing. If useful, run:

```bash
bash ${CODEX_PLUGIN_ROOT}/scripts/team_brief.sh "<goal>"
```

3. Split the work into three tracks:
   - planning
   - execution
   - verification
4. Only use sub-agents when the user explicitly asks for delegation, parallel agents, or sub-agents.
5. Keep ownership clean. Each workstream should have a disjoint write scope when parallel work is used.
6. End with verification status, remaining risks, and the next best follow-up.

## Workflow

### 1. Team Brief

Capture:
- goal
- constraints
- likely files or systems involved
- test and verification surface
- risks that would require a pause before proceeding

### 2. Workstream Design

Prefer 2-4 workstreams max. Good defaults:
- `plan`: repo reading, assumptions, architecture decisions
- `build`: code changes with explicit file ownership
- `verify`: tests, review, or manual checks

Do not create parallel work just for appearance. If the task is small or tightly coupled, keep it sequential.

### 3. Delegation Rules

- If the user did not ask for sub-agents, execute the work yourself and preserve the same plan/build/verify structure.
- If the user did ask for sub-agents, keep the critical path local and delegate bounded side work.
- Do not give multiple workers overlapping write ownership.
- Do not wait on sidecar work unless you are blocked on it.

### 4. Verification

Always verify at the level the task deserves:
- run targeted tests when code changes are made
- do a review pass for regressions and missing edge cases
- call out anything not verified

### 5. Closeout

Return:
- what changed
- how it was verified
- open risks or assumptions
- the most useful next step

## Guardrails

- Respect existing user changes and never revert unrelated work.
- Ask before destructive actions or hidden-risk decisions.
- Keep updates short and frequent while working.
- Favor concrete outcomes over performative planning.
