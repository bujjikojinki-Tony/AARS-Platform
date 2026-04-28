# Safety Software V&V Functional Safety Skill Workspace

This workspace is prepared for `skill-creator` style iteration runs.

## Current status

- Skill package is ready
- `evals/evals.json` is ready
- `iteration-1/` directory structure is ready
- per-eval `eval_metadata.json` files are ready
- actual `claude` CLI execution is currently blocked because the local CLI is not logged in

Observed blocker from local probe:

```text
Not logged in · Please run /login
```

## Iteration layout

```text
Safety_Software_VV_Functional_Safety_Skill-workspace/
  iteration-1/
    eval-1-standards-role-clarity/
      eval_metadata.json
      with_skill/
        outputs/
      without_skill/
        outputs/
    eval-2-change-impact-screening/
      eval_metadata.json
      with_skill/
        outputs/
      without_skill/
        outputs/
    eval-3-nuclear-vv-gap-review/
      eval_metadata.json
      with_skill/
        outputs/
      without_skill/
        outputs/
```

## Intended next step

After Claude CLI login is available, run each eval twice:

1. `with_skill`
2. `without_skill`

Then save:

- deliverable output files into each `outputs/` directory
- timing data into `timing.json`
- grading results into `grading.json`
- benchmark output into `iteration-1/benchmark.json`

## Notes

This skill is being treated as a new skill, so the baseline configuration is `without_skill`.
