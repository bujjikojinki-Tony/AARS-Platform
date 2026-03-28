#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: team_brief.sh \"<goal>\"" >&2
  exit 1
fi

goal="$1"

cat <<EOF
# Team Brief

Goal: $goal

Tracks:
- Planning: identify constraints, file scope, and success criteria.
- Execution: make the smallest coherent change with clear ownership.
- Verification: run the narrowest strong check and note any gaps.

Risk Checks:
- External dependencies or network access needed?
- Destructive or irreversible operations involved?
- User changes in the same write scope?

Closeout:
- Summarize the change in plain language.
- State what was verified.
- List the next best follow-up.
EOF
